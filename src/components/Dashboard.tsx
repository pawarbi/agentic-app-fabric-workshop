import React from 'react';
import { TrendingUp, TrendingDown, DollarSign, CreditCard, PiggyBank, Shield } from 'lucide-react';
import { useUser } from '../contexts/UserContext';
import type { Account, Transaction } from '../types/banking';

interface DashboardProps {
  accounts: Account[];
  recentTransactions: Transaction[];
}

const Dashboard: React.FC<DashboardProps> = ({ accounts, recentTransactions }) => {
  const { currentUser } = useUser();
  
  const totalBalance = accounts.reduce((sum, account) => sum + account.balance, 0);
  const monthlySpending = recentTransactions
    .filter(t => t.type === 'payment' && new Date(t.created_at).getMonth() === new Date().getMonth())
    .reduce((sum, t) => sum + t.amount, 0);

  // Get first name from full name
  const firstName = currentUser?.name.split(' ')[0] || 'Guest';

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-800 to-blue-600 rounded-2xl p-8 text-white">
        <h2 className="text-3xl font-bold mb-2">Welcome back, {firstName}!</h2>
        <p className="text-blue-100 mb-6">Here's an overview of your financial activity</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white/10 backdrop-blur rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm">Total Balance</p>
                <p className="text-2xl font-bold">${totalBalance.toLocaleString()}</p>
              </div>
              <DollarSign className="h-8 w-8 text-blue-200" />
            </div>
          </div>
          <div className="bg-white/10 backdrop-blur rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm">Monthly Spending</p>
                <p className="text-2xl font-bold">${monthlySpending.toLocaleString()}</p>
              </div>
              <TrendingDown className="h-8 w-8 text-blue-200" />
            </div>
          </div>
          <div className="bg-white/10 backdrop-blur rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm">Active Accounts</p>
                <p className="text-2xl font-bold">{accounts.length}</p>
              </div>
              <Shield className="h-8 w-8 text-blue-200" />
            </div>
          </div>
        </div>
      </div>

      {/* Accounts Grid */}
      <div>
        <h3 className="text-xl font-bold mb-4 text-gray-800">Your Accounts</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {accounts.map((account) => (
            <div key={account.id} className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  {account.account_type === 'checking' ? (
                    <CreditCard className="h-8 w-8 text-blue-600" />
                  ) : (
                    <PiggyBank className="h-8 w-8 text-green-600" />
                  )}
                  <div>
                    <h4 className="font-semibold text-gray-800">{account.name}</h4>
                    <p className="text-sm text-gray-500 capitalize">{account.account_type}</p>
                  </div>
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-500">Balance</p>
                <p className="text-2xl font-bold text-gray-800">${account.balance.toLocaleString()}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Transactions */}
      <div>
        <h3 className="text-xl font-bold mb-4 text-gray-800">Recent Transactions</h3>
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {recentTransactions.slice(0, 5).map((transaction) => (
                  <tr key={transaction.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(transaction.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">{transaction.description}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{transaction.category}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                      <span className={transaction.type === 'payment' ? 'text-red-600' : 'text-green-600'}>
                        {transaction.type === 'payment' ? '-' : '+'}${transaction.amount.toLocaleString()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;