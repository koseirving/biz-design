'use client';

import { useState } from 'react';

interface RegisterFormProps {
  onSubmit: (email: string, password: string) => Promise<void>;
  loading?: boolean;
}

export default function RegisterForm({ onSubmit, loading = false }: RegisterFormProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<{ 
    email?: string; 
    password?: string; 
    confirmPassword?: string 
  }>({});

  const validateEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validatePassword = (password: string) => {
    const minLength = password.length >= 8;
    const hasDigit = /\d/.test(password);
    const hasUpper = /[A-Z]/.test(password);
    const hasLower = /[a-z]/.test(password);
    
    return { minLength, hasDigit, hasUpper, hasLower };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    // Validation
    const newErrors: { email?: string; password?: string; confirmPassword?: string } = {};
    
    if (!email) {
      newErrors.email = 'Email is required';
    } else if (!validateEmail(email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    if (!password) {
      newErrors.password = 'Password is required';
    } else {
      const passwordValidation = validatePassword(password);
      if (!passwordValidation.minLength) {
        newErrors.password = 'Password must be at least 8 characters long';
      } else if (!passwordValidation.hasDigit) {
        newErrors.password = 'Password must contain at least one digit';
      } else if (!passwordValidation.hasUpper) {
        newErrors.password = 'Password must contain at least one uppercase letter';
      } else if (!passwordValidation.hasLower) {
        newErrors.password = 'Password must contain at least one lowercase letter';
      }
    }
    
    if (!confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      await onSubmit(email, password);
    } catch (error) {
      console.error('Registration failed:', error);
    }
  };

  const passwordValidation = validatePassword(password);

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg px-8 pt-6 pb-8 mb-4">
        <div className="mb-6 text-center">
          <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-2">
            Create Account
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Join Biz Design today
          </p>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label 
              className="block text-gray-700 dark:text-gray-300 text-sm font-bold mb-2" 
              htmlFor="email"
            >
              Email
            </label>
            <input
              className={`shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 dark:text-gray-300 dark:bg-gray-700 leading-tight focus:outline-none focus:shadow-outline ${
                errors.email ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
              }`}
              id="email"
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
            />
            {errors.email && (
              <p className="text-red-500 text-xs italic mt-1">{errors.email}</p>
            )}
          </div>
          
          <div className="mb-4">
            <label 
              className="block text-gray-700 dark:text-gray-300 text-sm font-bold mb-2" 
              htmlFor="password"
            >
              Password
            </label>
            <input
              className={`shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 dark:text-gray-300 dark:bg-gray-700 leading-tight focus:outline-none focus:shadow-outline ${
                errors.password ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
              }`}
              id="password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
            />
            {errors.password && (
              <p className="text-red-500 text-xs italic mt-1">{errors.password}</p>
            )}
            
            {password && (
              <div className="mt-2 text-xs">
                <div className={`${passwordValidation.minLength ? 'text-green-500' : 'text-red-500'}`}>
                  ✓ At least 8 characters
                </div>
                <div className={`${passwordValidation.hasDigit ? 'text-green-500' : 'text-red-500'}`}>
                  ✓ Contains a digit
                </div>
                <div className={`${passwordValidation.hasUpper ? 'text-green-500' : 'text-red-500'}`}>
                  ✓ Contains an uppercase letter
                </div>
                <div className={`${passwordValidation.hasLower ? 'text-green-500' : 'text-red-500'}`}>
                  ✓ Contains a lowercase letter
                </div>
              </div>
            )}
          </div>
          
          <div className="mb-6">
            <label 
              className="block text-gray-700 dark:text-gray-300 text-sm font-bold mb-2" 
              htmlFor="confirmPassword"
            >
              Confirm Password
            </label>
            <input
              className={`shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 dark:text-gray-300 dark:bg-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline ${
                errors.confirmPassword ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
              }`}
              id="confirmPassword"
              type="password"
              placeholder="Confirm your password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={loading}
            />
            {errors.confirmPassword && (
              <p className="text-red-500 text-xs italic">{errors.confirmPassword}</p>
            )}
          </div>
          
          <div className="flex items-center justify-between">
            <button
              className={`bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full ${
                loading ? 'opacity-50 cursor-not-allowed' : ''
              }`}
              type="submit"
              disabled={loading}
            >
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
          </div>
        </form>
        
        <div className="text-center mt-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Already have an account?{' '}
            <button
              type="button"
              className="text-blue-500 hover:text-blue-700 font-bold"
              onClick={() => {/* Navigate to login */}}
            >
              Sign in here
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}