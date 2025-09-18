import { PrismaClient } from '@prisma/client'
import bcrypt from 'bcryptjs'

const prisma = new PrismaClient()

async function main() {
  console.log('🌱 Starting database seed...')

  // Create categories
  const categories = await Promise.all([
    prisma.category.upsert({
      where: { name: 'Frontend' },
      update: {},
      create: {
        name: 'Frontend',
        description: 'Client-side development issues',
        color: '#3b82f6',
      },
    }),
    prisma.category.upsert({
      where: { name: 'Backend' },
      update: {},
      create: {
        name: 'Backend',
        description: 'Server-side development issues',
        color: '#10b981',
      },
    }),
    prisma.category.upsert({
      where: { name: 'Database' },
      update: {},
      create: {
        name: 'Database',
        description: 'Database-related issues',
        color: '#f59e0b',
      },
    }),
    prisma.category.upsert({
      where: { name: 'DevOps' },
      update: {},
      create: {
        name: 'DevOps',
        description: 'Deployment and infrastructure issues',
        color: '#ef4444',
      },
    }),
    prisma.category.upsert({
      where: { name: 'Mobile' },
      update: {},
      create: {
        name: 'Mobile',
        description: 'Mobile development issues',
        color: '#8b5cf6',
      },
    }),
    prisma.category.upsert({
      where: { name: 'API' },
      update: {},
      create: {
        name: 'API',
        description: 'API development and integration issues',
        color: '#06b6d4',
      },
    }),
  ])

  console.log('✅ Categories created:', categories.length)

  // Create technologies
  const technologies = await Promise.all([
    prisma.technology.upsert({
      where: { name: 'javascript' },
      update: {},
      create: { name: 'javascript', version: 'ES2023' },
    }),
    prisma.technology.upsert({
      where: { name: 'typescript' },
      update: {},
      create: { name: 'typescript', version: '5.0' },
    }),
    prisma.technology.upsert({
      where: { name: 'react' },
      update: {},
      create: { name: 'react', version: '18.0' },
    }),
    prisma.technology.upsert({
      where: { name: 'next.js' },
      update: {},
      create: { name: 'next.js', version: '14.0' },
    }),
    prisma.technology.upsert({
      where: { name: 'node.js' },
      update: {},
      create: { name: 'node.js', version: '20.0' },
    }),
    prisma.technology.upsert({
      where: { name: 'python' },
      update: {},
      create: { name: 'python', version: '3.11' },
    }),
    prisma.technology.upsert({
      where: { name: 'postgresql' },
      update: {},
      create: { name: 'postgresql', version: '15.0' },
    }),
    prisma.technology.upsert({
      where: { name: 'prisma' },
      update: {},
      create: { name: 'prisma', version: '5.0' },
    }),
    prisma.technology.upsert({
      where: { name: 'tailwindcss' },
      update: {},
      create: { name: 'tailwindcss', version: '3.4' },
    }),
    prisma.technology.upsert({
      where: { name: 'docker' },
      update: {},
      create: { name: 'docker', version: '24.0' },
    }),
  ])

  console.log('✅ Technologies created:', technologies.length)

  // Create admin user
  const adminPassword = await bcrypt.hash('admin123!', 12)
  const adminUser = await prisma.user.upsert({
    where: { email: 'admin@debugkb.com' },
    update: {},
    create: {
      email: 'admin@debugkb.com',
      name: 'Admin User',
      role: 'ADMIN',
      password: adminPassword,
    },
  })

  // Create demo user
  const demoPassword = await bcrypt.hash('demo123!', 12)
  const demoUser = await prisma.user.upsert({
    where: { email: 'demo@debugkb.com' },
    update: {},
    create: {
      email: 'demo@debugkb.com',
      name: 'Demo User',
      role: 'USER',
      password: demoPassword,
    },
  })

  console.log('✅ Users created')

  // Create sample issues
  const frontendCategory = categories.find(c => c.name === 'Frontend')!
  const backendCategory = categories.find(c => c.name === 'Backend')!
  const reactTech = technologies.find(t => t.name === 'react')!
  const nodeTech = technologies.find(t => t.name === 'node.js')!

  const issues = await Promise.all([
    prisma.issue.create({
      data: {
        title: 'React useState not updating component',
        description: 'I have a React component where useState is not triggering re-renders. The state value changes but the component doesn\'t update in the UI.',
        errorMessage: 'Component not re-rendering after state update',
        codeSnippet: `function MyComponent() {
  const [count, setCount] = useState(0);
  
  const handleClick = () => {
    setCount(count + 1);
    console.log(count); // Still shows old value
  };
  
  return <button onClick={handleClick}>{count}</button>;
}`,
        severity: 'MEDIUM',
        status: 'RESOLVED',
        authorId: demoUser.id,
        categoryId: frontendCategory.id,
        technologies: {
          connect: [{ id: reactTech.id }],
        },
      },
    }),
    prisma.issue.create({
      data: {
        title: 'Node.js CORS error in Express API',
        description: 'Getting CORS policy error when making requests from frontend to my Express.js API. Browser blocks the requests.',
        errorMessage: 'Access to fetch at \'http://localhost:3001/api/users\' from origin \'http://localhost:3000\' has been blocked by CORS policy',
        stackTrace: `Error: CORS policy
    at XMLHttpRequest.xhr.onreadystatechange (app.js:123:45)`,
        severity: 'HIGH',
        status: 'OPEN',
        environment: 'development',
        authorId: demoUser.id,
        categoryId: backendCategory.id,
        technologies: {
          connect: [{ id: nodeTech.id }],
        },
      },
    }),
  ])

  // Create solutions for the first issue
  await prisma.solution.create({
    data: {
      title: 'Use functional state updates',
      description: 'The issue is that you\'re using the current state value in the setter function. React state updates are asynchronous, so the console.log will show the old value. Use functional updates instead.',
      codeSnippet: `function MyComponent() {
  const [count, setCount] = useState(0);
  
  const handleClick = () => {
    setCount(prevCount => prevCount + 1);
    // Or use useEffect to see the updated value
  };
  
  return <button onClick={handleClick}>{count}</button>;
}`,
      steps: [
        'Use functional state updates: setCount(prevCount => prevCount + 1)',
        'If you need to access the updated value, use useEffect with count as dependency',
        'Remember that setState is asynchronous, so console.log immediately after won\'t show the new value',
      ],
      isAccepted: true,
      effectiveness: 9,
      upvotes: 15,
      issueId: issues[0].id,
      authorId: adminUser.id,
    },
  })

  console.log('✅ Sample issues and solutions created')

  // Create some comments
  await Promise.all([
    prisma.comment.create({
      data: {
        content: 'This is a common React gotcha! Thanks for the clear explanation.',
        issueId: issues[0].id,
        authorId: demoUser.id,
        upvotes: 3,
      },
    }),
    prisma.comment.create({
      data: {
        content: 'Have you tried installing the cors middleware package?',
        issueId: issues[1].id,
        authorId: adminUser.id,
      },
    }),
  ])

  console.log('✅ Comments created')

  console.log('🎉 Database seeding completed!')
  console.log('\n📝 Demo accounts:')
  console.log('Admin: admin@debugkb.com / admin123!')
  console.log('User: demo@debugkb.com / demo123!')
}

main()
  .then(async () => {
    await prisma.$disconnect()
  })
  .catch(async (e) => {
    console.error('❌ Seeding failed:', e)
    await prisma.$disconnect()
    process.exit(1)
  })