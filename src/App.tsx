import React, { useState, useEffect } from 'react';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import Transactions from './components/Transactions';
import Transfer from './components/Transfer';
import Analytics from './components/Analytics';
import ChatBot from './components/ChatBot';
import SignUpModal from './components/SignUpModal';
import { MessageCircle, X } from 'lucide-react';
import { UserProvider, useUser } from './contexts/UserContext';

import ChatSessions from './components/ChatSessions';
import ToolAnalytics from './components/ToolAnalytics';

import type { Account, Transaction } from './types/banking';

const API_URL = 'http://127.0.0.1:5001/api';

function AppContent() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isSignUpOpen, setIsSignUpOpen] = useState(false);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const { currentUser, isLoading: userLoading } = useUser();

  useEffect(() => {
    // Show signup modal if no user is logged in
    if (!userLoading && !currentUser) {
      setIsSignUpOpen(true);
    }
  }, [currentUser, userLoading]);

  useEffect(() => {
    // Clear previous session data on app launch
    localStorage.removeItem('chatSessionId');
    console.log('🧹 Previous chat session cleared - new session will be created');
    
    if (currentUser) {
      loadBankingData();
    }
  }, [currentUser]);
  
  const loadBankingData = async () => {
    if (!currentUser) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const headers = {
        'X-User-Id': currentUser.id
      };

      const [accountsResponse, transactionsResponse] = await Promise.all([
        fetch(`${API_URL}/accounts`, { headers }),
        fetch(`${API_URL}/transactions`, { headers }),
      ]);
      
      if (!accountsResponse.ok || !transactionsResponse.ok) {
        throw new Error('Failed to fetch data from the server.');
      }
      
      const accountsData = await accountsResponse.json();
      const transactionsData = await transactionsResponse.json();
      setAccounts(accountsData);
      setTransactions(transactionsData);
    } catch (error) {
      console.error('Error loading banking data:', error);
      setError('Could not connect to the banking service. Please ensure the backend is running and refresh.');
    } finally {
      setLoading(false);
    }
  };

  const handleTransactionComplete = async (transactionData: Omit<Transaction, 'id' | 'created_at' | 'status'>, fromAccountName: string, toAccountName?: string) => {
    if (!currentUser) return;

    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/transactions`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-User-Id': currentUser.id
        },
        body: JSON.stringify({
          from_account_name: fromAccountName,
          to_account_name: toAccountName,
          amount: transactionData.amount,
          description: transactionData.description
        }),
      });

      if (!response.ok) {
        const errorResult = await response.json();
        throw new Error(errorResult.message || 'Failed to complete transaction.');
      }
      
      await loadBankingData();

    } catch (error: any) {
      console.error('Error completing transaction:', error);
      setError(error.message || 'An unexpected error occurred during the transaction.');
    } finally {
      setLoading(false);
    }
  };

  const handleAccountCreate = async (accountData: { account_type: 'checking' | 'savings', name: string, balance: number }) => {
    if (!currentUser) return;

    try {
      const response = await fetch(`${API_URL}/accounts`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-User-Id': currentUser.id
        },
        body: JSON.stringify(accountData),
      });
      
      if (!response.ok) throw new Error('Account creation failed.');
      const newAccount = await response.json();
      await loadBankingData();
      return newAccount;
    } catch (err) {
      console.error("Error creating account:", err);
      setError("There was an error creating the new account.");
      throw err;
    }
  };

  const renderContent = () => {
    if (userLoading || loading) {
      return <div className="text-center p-8">Loading Banking Data...</div>;
    }
    
    if (!currentUser) {
      return (
        <div className="text-center p-8">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 max-w-md mx-auto">
            <h3 className="text-lg font-semibold text-blue-900 mb-2">Welcome to SecureBank Demo</h3>
            <p className="text-blue-700 mb-4">Please create a demo account to get started</p>
            <button
              onClick={() => setIsSignUpOpen(true)}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
            >
              Create Demo Account
            </button>
          </div>
        </div>
      );
    }
    
    if (error) {
      return <div className="text-center p-8 text-red-600 bg-red-50 rounded-lg">{error}</div>;
    }

    switch (activeTab) {
      case 'dashboard':
        return <Dashboard accounts={accounts} recentTransactions={transactions} />;
      case 'transactions':
        return <Transactions transactions={transactions} accounts={accounts} />;
      case 'transfer':
        return <Transfer accounts={accounts} onTransactionComplete={handleTransactionComplete} onAccountCreate={handleAccountCreate} />;
      case 'analytics':
        return <Analytics transactions={transactions} accounts={accounts} />;
      case 'chat-sessions':
        return <ChatSessions />;
      case 'tool-analytics':
        return <ToolAnalytics />;
      default:
        return <Dashboard accounts={accounts} recentTransactions={transactions} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Layout 
        activeTab={activeTab} 
        onTabChange={setActiveTab}
        onSignUpClick={() => setIsSignUpOpen(true)}
      >
        {renderContent()}
      </Layout>
      
      <button 
        onClick={() => setIsChatOpen(!isChatOpen)} 
        className={`fixed bottom-6 right-6 p-4 rounded-full shadow-lg transition-all z-40 ${isChatOpen ? 'bg-red-600' : 'bg-blue-600'} text-white`}
      >
        {isChatOpen ? <X/> : <MessageCircle/>}
      </button>
      
      {isChatOpen && currentUser && (
        <div className="fixed bottom-24 right-6 w-96 h-[500px] bg-white rounded-xl shadow-2xl border z-30">
          <ChatBot userId={currentUser.id} />
        </div>
      )}
      
      <SignUpModal 
        isOpen={isSignUpOpen} 
        onClose={() => setIsSignUpOpen(false)} 
      />
    </div>
  );
}

function App() {
  return (
    <UserProvider>
      <AppContent />
    </UserProvider>
  );
}

export default App;