import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// Helper: a date N days from today
const today = new Date();
const inDays = (n: number) =>
  new Date(today.getTime() + n * 24 * 60 * 60 * 1000);

/**
 * Market benchmark matrix for Columbus, GA.
 * Rates are average monthly spend by category and company-size bracket.
 */
const BENCHMARKS: Array<{
  category: string;
  small: number;
  medium: number;
}> = [
  { category: 'Janitorial Services', small: 450, medium: 850 },
  { category: 'Commercial Insurance', small: 350, medium: 650 },
  { category: 'IT Support', small: 800, medium: 1500 },
  { category: 'HVAC Maintenance', small: 300, medium: 550 },
  { category: 'Office Equipment Lease', small: 200, medium: 380 },
  { category: 'Phone & Internet', small: 150, medium: 280 },
  { category: 'Software / SaaS', small: 250, medium: 500 },
  { category: 'Waste Management', small: 175, medium: 320 },
  { category: 'Payroll Services', small: 120, medium: 240 },
  { category: 'Security / Alarm Monitoring', small: 90, medium: 170 },
  { category: 'Medical Waste Disposal', small: 110, medium: 210 },
  { category: 'Uniform / Linen Service', small: 140, medium: 260 },
];

/**
 * Three realistic Columbus, GA small-business sample tenants.
 * Each has a distinct vendor portfolio with a deliberate mix of
 * Overpaying / Fair / Great Deal statuses and varied renewal timing.
 */
const COMPANIES = [
  {
    email: 'office@riversidefamilydental.com',
    name: 'Riverside Family Dental',
    slug: 'riverside-family-dental',
    industry: 'Dental Practice',
    companySizeBracket: 'SMALL',
    contactName: 'Dr. Angela Reyes',
    vendors: [
      { vendorName: 'Sparkle Medical Cleaning', category: 'Janitorial Services', currentRate: 620, frequency: 'MONTHLY', renewalDate: inDays(12), notes: 'Daily clinical-grade cleaning, 6 operatories' },
      { vendorName: 'Georgia Dental Insurance Group', category: 'Commercial Insurance', currentRate: 360, frequency: 'MONTHLY', renewalDate: inDays(90), notes: 'Malpractice + general liability bundle' },
      { vendorName: 'MediTech IT Partners', category: 'IT Support', currentRate: 1050, frequency: 'MONTHLY', renewalDate: inDays(55), notes: 'HIPAA-compliant managed IT & backups' },
      { vendorName: 'Coolair HVAC', category: 'HVAC Maintenance', currentRate: 300, frequency: 'MONTHLY', renewalDate: inDays(200), notes: 'Quarterly service + filtration' },
      { vendorName: 'BioClean Medical Waste', category: 'Medical Waste Disposal', currentRate: 145, frequency: 'MONTHLY', renewalDate: inDays(25), notes: 'Biohazard & sharps pickup, weekly' },
      { vendorName: 'DentalSoft Practice Mgmt', category: 'Software / SaaS', currentRate: 230, frequency: 'MONTHLY', renewalDate: inDays(150), notes: 'Scheduling, charting & billing suite' },
    ],
  },
  {
    email: 'hello@chattahoocheecoffee.com',
    name: 'Chattahoochee Coffee Roasters',
    slug: 'chattahoochee-coffee-roasters',
    industry: 'Cafe & Roastery',
    companySizeBracket: 'SMALL',
    contactName: 'Marcus Webb',
    vendors: [
      { vendorName: 'CleanBrew Janitorial', category: 'Janitorial Services', currentRate: 480, frequency: 'MONTHLY', renewalDate: inDays(40), notes: 'Nightly cafe & restroom cleaning' },
      { vendorName: 'Brewers Mutual Insurance', category: 'Commercial Insurance', currentRate: 410, frequency: 'MONTHLY', renewalDate: inDays(18), notes: 'Property, liability & food spoilage' },
      { vendorName: 'POSPro Systems', category: 'Software / SaaS', currentRate: 300, frequency: 'MONTHLY', renewalDate: inDays(60), notes: 'Point-of-sale + loyalty program' },
      { vendorName: 'Southern Waste Solutions', category: 'Waste Management', currentRate: 175, frequency: 'MONTHLY', renewalDate: inDays(110), notes: 'Trash, recycling & compost pickup' },
      { vendorName: 'FreshLinen Uniform Co', category: 'Uniform / Linen Service', currentRate: 130, frequency: 'MONTHLY', renewalDate: inDays(75), notes: 'Aprons, towels & barista uniforms' },
      { vendorName: 'ConnectFast Internet', category: 'Phone & Internet', currentRate: 165, frequency: 'MONTHLY', renewalDate: inDays(5), notes: 'Business fiber + VoIP lines' },
    ],
  },
  {
    email: 'service@fountaincityauto.com',
    name: 'Fountain City Auto Repair',
    slug: 'fountain-city-auto-repair',
    industry: 'Auto Repair',
    companySizeBracket: 'MEDIUM',
    contactName: 'Travis Boone',
    vendors: [
      { vendorName: 'Guardian Garage Insurance', category: 'Commercial Insurance', currentRate: 720, frequency: 'MONTHLY', renewalDate: inDays(28), notes: 'Garage liability + garagekeepers' },
      { vendorName: 'AutoData Software', category: 'Software / SaaS', currentRate: 480, frequency: 'MONTHLY', renewalDate: inDays(95), notes: 'Estimating, parts catalog & invoicing' },
      { vendorName: 'Heavy Duty Waste & Oil', category: 'Waste Management', currentRate: 410, frequency: 'MONTHLY', renewalDate: inDays(22), notes: 'Used oil, tires & hazardous disposal' },
      { vendorName: 'ProTech IT Services', category: 'IT Support', currentRate: 1450, frequency: 'MONTHLY', renewalDate: inDays(130), notes: 'Shop network, cameras & POS support' },
      { vendorName: 'ShopGuard Security', category: 'Security / Alarm Monitoring', currentRate: 230, frequency: 'MONTHLY', renewalDate: inDays(14), notes: '24/7 alarm + camera monitoring' },
      { vendorName: 'MechWear Uniforms', category: 'Uniform / Linen Service', currentRate: 300, frequency: 'MONTHLY', renewalDate: inDays(65), notes: 'Mechanic uniforms & shop rags, 15 staff' },
    ],
  },
];

async function main() {
  // Clear existing data (order matters for FK constraints)
  await prisma.vendorContract.deleteMany();
  await prisma.marketBenchmark.deleteMany();
  await prisma.user.deleteMany();

  // Seed market benchmarks for both SMALL and MEDIUM brackets
  let benchmarkCount = 0;
  for (const b of BENCHMARKS) {
    await prisma.marketBenchmark.create({
      data: {
        category: b.category,
        companySizeBracket: 'SMALL',
        location: 'Columbus, GA',
        localAvgRateMonthly: b.small,
        localAvgRateAnnual: b.small * 12,
      },
    });
    await prisma.marketBenchmark.create({
      data: {
        category: b.category,
        companySizeBracket: 'MEDIUM',
        location: 'Columbus, GA',
        localAvgRateMonthly: b.medium,
        localAvgRateAnnual: b.medium * 12,
      },
    });
    benchmarkCount += 2;
  }

  // Seed companies and their vendor contracts
  let vendorCount = 0;
  for (const company of COMPANIES) {
    const { vendors, ...companyData } = company;
    const user = await prisma.user.create({ data: companyData });

    for (const vendor of vendors) {
      await prisma.vendorContract.create({
        data: { ...vendor, userId: user.id },
      });
      vendorCount++;
    }
  }

  console.log('✅ Database seeded successfully!');
  console.log(`   • ${COMPANIES.length} sample companies`);
  COMPANIES.forEach((c) =>
    console.log(`       - ${c.name} (${c.industry}, ${c.companySizeBracket}) → /rate-watch/${c.slug}`)
  );
  console.log(`   • ${benchmarkCount} market benchmarks (SMALL + MEDIUM brackets)`);
  console.log(`   • ${vendorCount} vendor contracts`);
}

main()
  .catch((e) => {
    console.error('Error seeding database:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
