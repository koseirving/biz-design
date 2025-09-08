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
      newErrors.email = 'メールアドレスが必要です';
    } else if (!validateEmail(email)) {
      newErrors.email = '有効なメールアドレスを入力してください';
    }
    
    if (!password) {
      newErrors.password = 'パスワードが必要です';
    } else {
      const passwordValidation = validatePassword(password);
      if (!passwordValidation.minLength) {
        newErrors.password = 'パスワードは8文字以上である必要があります';
      } else if (!passwordValidation.hasDigit) {
        newErrors.password = 'パスワードには少なくとも1つの数字を含む必要があります';
      } else if (!passwordValidation.hasUpper) {
        newErrors.password = 'パスワードには少なくとも1つの大文字を含む必要があります';
      } else if (!passwordValidation.hasLower) {
        newErrors.password = 'パスワードには少なくとも1つの小文字を含む必要があります';
      }
    }
    
    if (!confirmPassword) {
      newErrors.confirmPassword = 'パスワードを確認してください';
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = 'パスワードが一致しません';
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
      <div className="bg-white  shadow-lg rounded-lg px-8 pt-6 pb-8 mb-4">
        <div className="mb-6 text-center">
          <h2 className="text-2xl font-bold text-neutral-text-dark  mb-2">
            アカウント作成
          </h2>
          <p className="text-neutral-text-light ">
            ビズデザインに参加しましょう
          </p>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label 
              className="block text-neutral-text-dark  text-sm font-bold mb-2" 
              htmlFor="email"
            >
              メールアドレス
            </label>
            <input
              className={`shadow appearance-none border rounded w-full py-2 px-3 text-neutral-text-dark   leading-tight focus:outline-none focus:shadow-outline ${
                errors.email ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
              }`}
              id="email"
              type="email"
              placeholder="メールアドレスを入力"
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
              className="block text-neutral-text-dark  text-sm font-bold mb-2" 
              htmlFor="password"
            >
              パスワード
            </label>
            <input
              className={`shadow appearance-none border rounded w-full py-2 px-3 text-neutral-text-dark   leading-tight focus:outline-none focus:shadow-outline ${
                errors.password ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
              }`}
              id="password"
              type="password"
              placeholder="パスワードを入力"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
            />
            {errors.password && (
              <p className="text-red-500 text-xs italic mt-1">{errors.password}</p>
            )}
            
            {password && (
              <div className="mt-2 text-xs">
                <div className={`${passwordValidation.minLength ? 'text-status-mountain-meadow' : 'text-red-500'}`}>
                  ✓ 8文字以上
                </div>
                <div className={`${passwordValidation.hasDigit ? 'text-status-mountain-meadow' : 'text-red-500'}`}>
                  ✓ 数字を含む
                </div>
                <div className={`${passwordValidation.hasUpper ? 'text-status-mountain-meadow' : 'text-red-500'}`}>
                  ✓ 大文字を含む
                </div>
                <div className={`${passwordValidation.hasLower ? 'text-status-mountain-meadow' : 'text-red-500'}`}>
                  ✓ 小文字を含む
                </div>
              </div>
            )}
          </div>
          
          <div className="mb-6">
            <label 
              className="block text-neutral-text-dark  text-sm font-bold mb-2" 
              htmlFor="confirmPassword"
            >
              パスワードの確認
            </label>
            <input
              className={`shadow appearance-none border rounded w-full py-2 px-3 text-neutral-text-dark   mb-3 leading-tight focus:outline-none focus:shadow-outline ${
                errors.confirmPassword ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
              }`}
              id="confirmPassword"
              type="password"
              placeholder="パスワードを再入力"
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
              className={`bg-primary-tory-blue hover:bg-primary-tory-blue/90 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full transition-colors ${
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
          <p className="text-sm text-neutral-text-light ">
            すでにアカウントをお持ちの方は{' '}
            <button
              type="button"
              className="text-primary-royal-blue hover:text-primary-tory-blue font-bold transition-colors"
              onClick={() => {/* Navigate to login */}}
            >
              こちらからログイン
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}