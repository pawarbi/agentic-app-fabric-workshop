import React, { useState, useEffect, useRef } from 'react';
import { ChevronDown, User as UserIcon, Check, UserPlus, LogOut } from 'lucide-react';
import { useUser } from '../contexts/UserContext';

interface User {
  id: string;
  name: string;
  email: string;
}

interface UserSwitcherProps {
  onSignUpClick: () => void;
}

import { API_URL } from '../apiConfig';

const UserSwitcher: React.FC<UserSwitcherProps> = ({ onSignUpClick }) => {
  const { currentUser, setCurrentUser } = useUser();
  const [isOpen, setIsOpen] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      loadUsers();
    }
  }, [isOpen]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/auth/users`);
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      }
    } catch (error) {
      console.error('Failed to load users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUserSwitch = (user: User) => {
    setCurrentUser(user);
    setIsOpen(false);
    // Reload to fetch new user's data
    window.location.reload();
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setIsOpen(false);
    window.location.reload();
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition"
      >
        <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-medium">
          {currentUser ? getInitials(currentUser.name) : <UserIcon className="h-4 w-4" />}
        </div>
        <div className="hidden md:block text-left">
          <p className="text-sm font-medium text-gray-700">
            {currentUser ? currentUser.name : 'Guest User'}
          </p>
          {currentUser && (
            <p className="text-xs text-gray-500">{currentUser.email}</p>
          )}
        </div>
        <ChevronDown className={`h-4 w-4 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
          {/* Current User Section */}
          {currentUser && (
            <>
              <div className="px-4 py-3 border-b border-gray-200">
                <p className="text-sm font-medium text-gray-900">{currentUser.name}</p>
                <p className="text-xs text-gray-500">{currentUser.email}</p>
                <p className="text-xs text-gray-400 mt-1">ID: {currentUser.id.slice(0, 16)}...</p>
              </div>
            </>
          )}

          {/* Switch User Section */}
          <div className="px-2 py-2">
            <p className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase">
              Switch Account
            </p>
            
            {loading ? (
              <div className="px-3 py-4 text-center text-sm text-gray-500">
                Loading users...
              </div>
            ) : users.length === 0 ? (
              <div className="px-3 py-4 text-center text-sm text-gray-500">
                No other users found
              </div>
            ) : (
              <div className="max-h-60 overflow-y-auto">
                {users.map((user) => (
                  <button
                    key={user.id}
                    onClick={() => handleUserSwitch(user)}
                    className={`w-full px-3 py-2 text-left hover:bg-gray-50 rounded-md flex items-center justify-between transition ${
                      currentUser?.id === user.id ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <div className="h-8 w-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white text-xs font-medium">
                        {getInitials(user.name)}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{user.name}</p>
                        <p className="text-xs text-gray-500">{user.email}</p>
                      </div>
                    </div>
                    {currentUser?.id === user.id && (
                      <Check className="h-4 w-4 text-blue-600" />
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="border-t border-gray-200 mt-2 pt-2 px-2">
            <button
              onClick={() => {
                setIsOpen(false);
                onSignUpClick();
              }}
              className="w-full px-3 py-2 text-left hover:bg-gray-50 rounded-md flex items-center space-x-2 text-sm text-gray-700 transition"
            >
              <UserPlus className="h-4 w-4" />
              <span>Create New Demo Account</span>
            </button>
            
            {currentUser && (
              <button
                onClick={handleLogout}
                className="w-full px-3 py-2 text-left hover:bg-gray-50 rounded-md flex items-center space-x-2 text-sm text-red-600 transition"
              >
                <LogOut className="h-4 w-4" />
                <span>Sign Out</span>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default UserSwitcher;
