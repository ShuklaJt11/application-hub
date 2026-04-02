import { describe, expect, it } from 'vitest';

import { loginSchema, signupSchema } from './schemas';

describe('auth schemas', () => {
  it('accepts valid login credentials', () => {
    const result = loginSchema.safeParse({
      email: 'user@example.com',
      password: 'secret123',
    });

    expect(result.success).toBe(true);
  });

  it('rejects invalid login email', () => {
    const result = loginSchema.safeParse({
      email: 'not-an-email',
      password: 'secret123',
    });

    expect(result.success).toBe(false);
    expect(result.error?.issues[0]?.message).toBe('Invalid email format');
  });

  it('accepts valid signup data', () => {
    const result = signupSchema.safeParse({
      username: 'janedoe',
      first_name: 'Jane',
      last_name: 'Doe',
      email: 'jane@example.com',
      password: 'Password123',
      confirmPassword: 'Password123',
    });

    expect(result.success).toBe(true);
  });

  it('rejects weak signup passwords', () => {
    const result = signupSchema.safeParse({
      username: 'janedoe',
      first_name: 'Jane',
      last_name: 'Doe',
      email: 'jane@example.com',
      password: 'password',
      confirmPassword: 'password',
    });

    expect(result.success).toBe(false);
    expect(result.error?.issues.map((issue) => issue.message)).toContain(
      'Password must contain at least one uppercase letter'
    );
  });

  it('rejects mismatched signup passwords', () => {
    const result = signupSchema.safeParse({
      username: 'janedoe',
      first_name: 'Jane',
      last_name: 'Doe',
      email: 'jane@example.com',
      password: 'Password123',
      confirmPassword: 'Password456',
    });

    expect(result.success).toBe(false);
    expect(result.error?.issues[0]?.message).toBe('Passwords do not match');
  });

  it('rejects invalid usernames', () => {
    const result = signupSchema.safeParse({
      username: 'Jane Doe',
      first_name: 'Jane',
      last_name: 'Doe',
      email: 'jane@example.com',
      password: 'Password123',
      confirmPassword: 'Password123',
    });

    expect(result.success).toBe(false);
    expect(result.error?.issues[0]?.message).toBe(
      'Username can only contain lowercase letters, numbers, and underscores'
    );
  });
});
