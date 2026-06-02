import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  // Clear existing data
  await prisma.vendorContract.deleteMany();
  await prisma.marketBenchmark.deleteMany();
  await prisma.user.deleteMany();

  // Create a test user
  const user = await prisma.user.create({
    data: {
      email: 'demo@echoframe.local',
      name: 'Demo Business Owner',
    },
  });

  // Create market benchmarks for Columbus, GA area (Small businesses 1-10 employees)
  const benchmarks = [
    {
      category: 'Janitorial Services',
      companySizeBracket: 'SMALL',
      location: 'Columbus, GA',
      localAvgRateMonthly: 450,
      localAvgRateAnnual: 5400,
    },
    {
      category: 'Commercial Insurance',
      companySizeBracket: 'SMALL',
      location: 'Columbus, GA',
      localAvgRateMonthly: 350,
      localAvgRateAnnual: 4200,
    },
    {
      category: 'IT Support',
      companySizeBracket: 'SMALL',
      location: 'Columbus, GA',
      localAvgRateMonthly: 800,
      localAvgRateAnnual: 9600,
    },
    {
      category: 'HVAC Maintenance',
      companySizeBracket: 'SMALL',
      location: 'Columbus, GA',
      localAvgRateMonthly: 300,
      localAvgRateAnnual: 3600,
    },
    {
      category: 'Office Equipment Lease',
      companySizeBracket: 'SMALL',
      location: 'Columbus, GA',
      localAvgRateMonthly: 200,
      localAvgRateAnnual: 2400,
    },
    {
      category: 'Phone & Internet',
      companySizeBracket: 'SMALL',
      location: 'Columbus, GA',
      localAvgRateMonthly: 150,
      localAvgRateAnnual: 1800,
    },
  ];

  for (const benchmark of benchmarks) {
    await prisma.marketBenchmark.create({
      data: benchmark,
    });
  }

  // Create realistic vendor contracts with mix of overpaying and fair rates
  const today = new Date();
  const nextMonth = new Date(today.getTime() + 30 * 24 * 60 * 60 * 1000);
  const twoMonths = new Date(today.getTime() + 60 * 24 * 60 * 60 * 1000);
  const fourMonths = new Date(today.getTime() + 120 * 24 * 60 * 60 * 1000);
  const sixMonths = new Date(today.getTime() + 180 * 24 * 60 * 60 * 1000);

  const contracts = [
    {
      vendorName: 'Superior Cleaning Solutions',
      category: 'Janitorial Services',
      currentRate: 650, // OVERPAYING (vs $450)
      frequency: 'MONTHLY',
      renewalDate: nextMonth,
      notes: 'Daily office cleaning, M-F',
    },
    {
      vendorName: 'Guardian Business Insurance',
      category: 'Commercial Insurance',
      currentRate: 350, // FAIR (vs $350)
      frequency: 'MONTHLY',
      renewalDate: twoMonths,
      notes: 'General liability and property insurance',
    },
    {
      vendorName: 'TechPro IT Solutions',
      category: 'IT Support',
      currentRate: 950, // OVERPAYING (vs $800)
      frequency: 'MONTHLY',
      renewalDate: fourMonths,
      notes: 'Managed IT services and helpdesk support',
    },
    {
      vendorName: 'Elite HVAC Services',
      category: 'HVAC Maintenance',
      currentRate: 300, // FAIR (vs $300)
      frequency: 'MONTHLY',
      renewalDate: sixMonths,
      notes: 'Quarterly maintenance and emergency service',
    },
    {
      vendorName: 'Global Office Leasing',
      category: 'Office Equipment Lease',
      currentRate: 250, // OVERPAYING (vs $200)
      frequency: 'MONTHLY',
      renewalDate: new Date(today.getTime() + 45 * 24 * 60 * 60 * 1000),
      notes: 'Copier and printer lease agreement',
    },
    {
      vendorName: 'ConnectTech Communications',
      category: 'Phone & Internet',
      currentRate: 200, // OVERPAYING (vs $150)
      frequency: 'MONTHLY',
      renewalDate: new Date(today.getTime() + 15 * 24 * 60 * 60 * 1000),
      notes: 'Business-grade internet and phone service',
    },
  ];

  for (const contract of contracts) {
    await prisma.vendorContract.create({
      data: {
        ...contract,
        userId: user.id,
      },
    });
  }

  console.log('✅ Database seeded successfully!');
  console.log(`   • Created user: ${user.email}`);
  console.log(`   • Created ${benchmarks.length} market benchmarks`);
  console.log(`   • Created ${contracts.length} vendor contracts`);
}

main()
  .catch((e) => {
    console.error('Error seeding database:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
