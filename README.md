# 🔧 Code Debugging Knowledge Base

A full-stack application that stores and retrieves debugging solutions from past developer issues, providing AI-powered suggestions using PostgreSQL, Node.js, OpenAI API, and Next.js.

![Tech Stack](https://img.shields.io/badge/Tech_Stack-Next.js_14-blue)
![Database](https://img.shields.io/badge/Database-PostgreSQL-blue)
![AI](https://img.shields.io/badge/AI-OpenAI_GPT--4-green)
![Deployment](https://img.shields.io/badge/Deploy-Vercel-black)

## ✨ Features

- 🔍 **Smart Search**: Full-text search with filters by technology, category, and severity
- 🤖 **AI Suggestions**: Generate solutions using OpenAI based on similar past issues
- 📊 **Issue Management**: Create, update, and track debugging issues with detailed metadata
- 💡 **Solution Library**: Community-driven solutions with effectiveness ratings
- 🏷️ **Categorization**: Organize issues by technology stack, error types, and difficulty
- 👥 **User Authentication**: Secure access with OAuth (Google, GitHub) and credentials
- 📈 **Analytics**: Track popular searches and trending technologies
- 🌙 **Dark Mode**: Modern UI with light/dark theme support
- 📱 **Responsive Design**: Works seamlessly on desktop and mobile devices

## 🏗️ Tech Stack

### Frontend
- **Framework**: Next.js 14 (React 18)
- **Styling**: Tailwind CSS with custom design system
- **UI Components**: Headless UI, Heroicons
- **State Management**: React Hooks + Context API
- **Authentication**: NextAuth.js

### Backend
- **Runtime**: Node.js 18+
- **Database**: PostgreSQL 15 with Prisma ORM
- **AI Integration**: OpenAI GPT-4 API
- **Authentication**: JWT tokens, OAuth providers
- **API**: RESTful API with TypeScript

### Infrastructure
- **Deployment**: Vercel (Frontend) + Railway/Neon (Database)
- **Development**: Docker Compose
- **Monitoring**: Built-in health checks and logging

## 🚀 Quick Start

### Prerequisites

- Node.js 18 or higher
- PostgreSQL 14+ (or use Docker)
- Git
- OpenAI API key

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/debugging-knowledge-base.git
cd debugging-knowledge-base
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Environment Setup

Copy the environment template and configure your variables:

```bash
cp .env.example .env.local
```

Edit `.env.local` with your configuration:

```env
# Database
DATABASE_URL="postgresql://username:password@localhost:5432/debugging_kb?schema=public"

# NextAuth.js
NEXTAUTH_URL="http://localhost:3000"
NEXTAUTH_SECRET="your-secret-key-here"

# OpenAI API
OPENAI_API_KEY="sk-your-openai-api-key"

# OAuth Providers (Optional)
GOOGLE_CLIENT_ID="your-google-client-id"
GOOGLE_CLIENT_SECRET="your-google-client-secret"
GITHUB_CLIENT_ID="your-github-client-id"
GITHUB_CLIENT_SECRET="your-github-client-secret"
```

### 4. Database Setup

```bash
# Start PostgreSQL (or use Docker)
docker-compose up -d database

# Run database migrations
npm run db:migrate

# Seed the database with sample data
npm run db:seed
```

### 5. Start Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the application.

## 🐳 Docker Development

For a complete development environment with all services:

```bash
# Start all services (app, database, redis, pgadmin)
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop all services
docker-compose down
```

Services will be available at:
- **App**: http://localhost:3000
- **Database**: localhost:5432
- **PgAdmin**: http://localhost:8080 (admin@debugkb.com / admin123)
- **Redis**: localhost:6379

## 📁 Project Structure

```
debugging-kb/
├── components/           # Reusable UI components
│   ├── Layout.tsx       # Main layout wrapper
│   ├── IssueList.tsx    # Issue listing component
│   ├── SearchBar.tsx    # Search functionality
│   └── ...
├── lib/                 # Utility libraries
│   ├── auth.ts          # Authentication configuration
│   ├── db.ts            # Database utilities
│   ├── openai.ts        # AI service integration
│   └── ...
├── pages/               # Next.js pages and API routes
│   ├── api/             # API endpoints
│   ├── issues/          # Issue pages
│   ├── auth/            # Authentication pages
│   └── ...
├── prisma/              # Database schema and migrations
│   ├── schema.prisma    # Database schema
│   ├── migrations/      # Migration files
│   └── seed.ts          # Database seeding
├── styles/              # Global styles
├── types/               # TypeScript type definitions
└── public/              # Static assets
```

## 🔑 API Endpoints

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/signin` - User login
- `POST /api/auth/signout` - User logout

### Issues
- `GET /api/issues` - List issues with search/filters
- `POST /api/issues` - Create new issue
- `GET /api/issues/[id]` - Get specific issue
- `PUT /api/issues/[id]` - Update issue
- `DELETE /api/issues/[id]` - Delete issue

### Solutions
- `GET /api/solutions` - List solutions
- `POST /api/solutions` - Create solution
- `PUT /api/solutions/[id]` - Update solution
- `DELETE /api/solutions/[id]` - Delete solution

### AI Suggestions
- `POST /api/ai/suggest` - Generate AI suggestion for issue

### Analytics
- `GET /api/stats` - Platform statistics
- `GET /api/search/trends` - Trending searches

## 🚀 Deployment

### Vercel Deployment (Recommended)

1. **Connect to Vercel**:
   ```bash
   npx vercel --prod
   ```

2. **Set Environment Variables** in Vercel dashboard:
   - `DATABASE_URL` - Your production PostgreSQL URL
   - `NEXTAUTH_SECRET` - Random secret for JWT
   - `OPENAI_API_KEY` - Your OpenAI API key
   - OAuth credentials (if using)

3. **Database Setup**:
   - Use [Neon](https://neon.tech) or [Supabase](https://supabase.com) for PostgreSQL
   - Run migrations: `npx prisma migrate deploy`
   - Seed database: `npm run db:seed`

### Alternative: Railway

1. **Create Railway Project**:
   ```bash
   npm install -g @railway/cli
   railway login
   railway init
   ```

2. **Add PostgreSQL**:
   ```bash
   railway add postgresql
   ```

3. **Deploy**:
   ```bash
   railway up
   ```

### Docker Production

```bash
# Build production image
docker build -t debugging-kb .

# Run container
docker run -p 3000:3000 \
  -e DATABASE_URL="your-production-db-url" \
  -e NEXTAUTH_SECRET="your-secret" \
  -e OPENAI_API_KEY="your-api-key" \
  debugging-kb
```

## 🔧 Configuration

### OpenAI Setup

1. Create an account at [OpenAI](https://openai.com)
2. Generate an API key
3. Add to environment variables
4. Configure rate limits and model preferences in `lib/openai.ts`

### OAuth Setup

#### Google OAuth
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:3000/api/auth/callback/google`

#### GitHub OAuth
1. Go to GitHub Settings > Developer settings > OAuth Apps
2. Create a new OAuth App
3. Set Authorization callback URL: `http://localhost:3000/api/auth/callback/github`

## 📊 Database Schema

Key entities and relationships:

- **Users**: Authentication and profile information
- **Issues**: Debugging problems with metadata
- **Solutions**: Community-provided fixes
- **Comments**: Discussion threads
- **Categories**: Issue organization
- **Technologies**: Tech stack tagging
- **AI Suggestions**: Generated recommendations

## 🧪 Testing

```bash
# Run unit tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run integration tests
npm run test:integration

# Run all tests with coverage
npm run test:coverage
```

## 📈 Performance & Monitoring

- **Database Indexing**: Optimized queries with proper indexes
- **Caching**: Redis for session and API response caching
- **Rate Limiting**: API endpoints protected from abuse
- **Error Tracking**: Comprehensive logging and error handling
- **Health Checks**: Built-in monitoring endpoints

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Use TypeScript for type safety
- Follow ESLint configuration
- Write tests for new features
- Update documentation
- Use conventional commit messages

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Next.js](https://nextjs.org) - React framework
- [Prisma](https://prisma.io) - Database ORM
- [OpenAI](https://openai.com) - AI API
- [Tailwind CSS](https://tailwindcss.com) - Styling
- [Vercel](https://vercel.com) - Deployment platform

## 📞 Support

- 📧 Email: support@debugkb.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/debugging-knowledge-base/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/debugging-knowledge-base/discussions)

---

**Made with ❤️ by developers, for developers**