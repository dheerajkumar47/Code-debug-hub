import { NextAuthOptions } from 'next-auth'
import { PrismaAdapter } from '@next-auth/prisma-adapter'
import GoogleProvider from 'next-auth/providers/google'
import GitHubProvider from 'next-auth/providers/github'
import CredentialsProvider from 'next-auth/providers/credentials'
import { prisma } from './db'
import bcrypt from 'bcryptjs'

export const authOptions: NextAuthOptions = {
  adapter: PrismaAdapter(prisma),
  providers: [
    // Google OAuth
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      authorization: {
        params: {
          prompt: 'consent',
          access_type: 'offline',
          response_type: 'code',
        },
      },
    }),
    
    // GitHub OAuth
    GitHubProvider({
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
    }),
    
    // Email/Password credentials
    CredentialsProvider({
      name: 'credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          throw new Error('Email and password required')
        }

        try {
          const user = await prisma.user.findUnique({
            where: {
              email: credentials.email,
            },
          })

          if (!user) {
            throw new Error('No user found with this email')
          }

          // For OAuth users, password might not be set
          if (!user.password) {
            throw new Error('Please sign in with your OAuth provider')
          }

          const isPasswordValid = await bcrypt.compare(
            credentials.password,
            user.password
          )

          if (!isPasswordValid) {
            throw new Error('Invalid password')
          }

          return {
            id: user.id,
            email: user.email,
            name: user.name,
            image: user.image,
            role: user.role,
          }
        } catch (error) {
          console.error('Auth error:', error)
          return null
        }
      },
    }),
  ],
  
  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  
  callbacks: {
    async jwt({ token, user, account }) {
      // Initial sign in
      if (account && user) {
        return {
          ...token,
          id: user.id,
          role: user.role,
          provider: account.provider,
        }
      }

      // Return previous token if the access token has not expired yet
      return token
    },
    
    async session({ session, token }) {
      // Send properties to the client
      if (token) {
        session.user.id = token.id as string
        session.user.role = token.role as string
        session.user.provider = token.provider as string
      }
      
      return session
    },
    
    async signIn({ user, account, profile }) {
      try {
        // Allow OAuth sign-ins
        if (account?.provider === 'google' || account?.provider === 'github') {
          return true
        }
        
        // For credentials, user is already validated in authorize()
        if (account?.provider === 'credentials') {
          return true
        }
        
        return false
      } catch (error) {
        console.error('SignIn callback error:', error)
        return false
      }
    },
    
    async redirect({ url, baseUrl }) {
      // Allows relative callback URLs
      if (url.startsWith('/')) return `${baseUrl}${url}`
      
      // Allows callback URLs on the same origin
      else if (new URL(url).origin === baseUrl) return url
      
      return baseUrl
    },
  },
  
  pages: {
    signIn: '/auth/signin',
    signUp: '/auth/signup',
    error: '/auth/error',
    verifyRequest: '/auth/verify-request',
  },
  
  events: {
    async signIn({ user, account, profile, isNewUser }) {
      console.log('User signed in:', { 
        userId: user.id, 
        provider: account?.provider,
        isNewUser 
      })
      
      // Update user's last login
      if (user.id) {
        await prisma.user.update({
          where: { id: user.id },
          data: { lastLoginAt: new Date() },
        }).catch(console.error)
      }
    },
    
    async createUser({ user }) {
      console.log('New user created:', user.id)
      
      // Set default role for new users
      await prisma.user.update({
        where: { id: user.id },
        data: { role: 'USER' },
      }).catch(console.error)
    },
  },
  
  debug: process.env.NODE_ENV === 'development',
}

// Utility functions for authentication
export const authUtils = {
  // Hash password for credentials signup
  async hashPassword(password: string): Promise<string> {
    return bcrypt.hash(password, 12)
  },

  // Verify password
  async verifyPassword(password: string, hashedPassword: string): Promise<boolean> {
    return bcrypt.compare(password, hashedPassword)
  },

  // Create user with credentials
  async createUser(email: string, password: string, name?: string) {
    const hashedPassword = await this.hashPassword(password)
    
    try {
      const user = await prisma.user.create({
        data: {
          email,
          password: hashedPassword,
          name,
          role: 'USER',
        },
      })
      
      return user
    } catch (error: any) {
      if (error.code === 'P2002') {
        throw new Error('User with this email already exists')
      }
      throw error
    }
  },

  // Check if user exists
  async userExists(email: string): Promise<boolean> {
    const user = await prisma.user.findUnique({
      where: { email },
    })
    return !!user
  },

  // Get user permissions
  getUserPermissions(role: string) {
    const permissions = {
      USER: [
        'read:own_issues',
        'create:issues',
        'update:own_issues',
        'delete:own_issues',
        'create:solutions',
        'create:comments',
      ],
      MODERATOR: [
        'read:all_issues',
        'update:all_issues',
        'delete:solutions',
        'delete:comments',
        'moderate:content',
      ],
      ADMIN: [
        'read:all',
        'create:all',
        'update:all',
        'delete:all',
        'manage:users',
        'manage:system',
      ],
    }
    
    // Include lower level permissions
    if (role === 'ADMIN') {
      return [...permissions.USER, ...permissions.MODERATOR, ...permissions.ADMIN]
    }
    if (role === 'MODERATOR') {
      return [...permissions.USER, ...permissions.MODERATOR]
    }
    return permissions.USER || []
  },

  // Check if user has permission
  hasPermission(userRole: string, requiredPermission: string): boolean {
    const userPermissions = this.getUserPermissions(userRole)
    return userPermissions.includes(requiredPermission)
  },

  // Validate email format
  isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  },

  // Validate password strength
  isValidPassword(password: string): { valid: boolean; message?: string } {
    if (password.length < 8) {
      return { valid: false, message: 'Password must be at least 8 characters long' }
    }
    
    if (!/(?=.*[a-z])/.test(password)) {
      return { valid: false, message: 'Password must contain at least one lowercase letter' }
    }
    
    if (!/(?=.*[A-Z])/.test(password)) {
      return { valid: false, message: 'Password must contain at least one uppercase letter' }
    }
    
    if (!/(?=.*\d)/.test(password)) {
      return { valid: false, message: 'Password must contain at least one number' }
    }
    
    if (!/(?=.*[@$!%*?&])/.test(password)) {
      return { valid: false, message: 'Password must contain at least one special character' }
    }
    
    return { valid: true }
  },
}

// TypeScript augmentation for NextAuth
declare module 'next-auth' {
  interface Session {
    user: {
      id: string
      email: string
      name?: string
      image?: string
      role: string
      provider: string
    }
  }
  
  interface User {
    role: string
    password?: string
    lastLoginAt?: Date
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    id: string
    role: string
    provider: string
  }
}