import { Button } from '@/components/ui/button';
import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-white">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center space-y-8">
          <h1 className="text-5xl sm:text-6xl font-bold tracking-tight">
            EchoFrame Intelligence
          </h1>
          <p className="text-xl sm:text-2xl text-slate-300 max-w-2xl mx-auto">
            Financial intelligence tools for small business owners
          </p>

          <div className="grid md:grid-cols-3 gap-6 mt-12">
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <h3 className="text-lg font-semibold mb-2">Rate Watch</h3>
              <p className="text-slate-400 mb-4">
                Benchmark your vendor contracts against market rates and identify savings opportunities
              </p>
              <Link href="/rate-watch">
                <Button variant="secondary" className="w-full">
                  Launch Rate Watch
                </Button>
              </Link>
            </div>

            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 opacity-50">
              <h3 className="text-lg font-semibold mb-2">More Coming Soon</h3>
              <p className="text-slate-400">
                Additional financial intelligence tools
              </p>
            </div>

            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 opacity-50">
              <h3 className="text-lg font-semibold mb-2">More Coming Soon</h3>
              <p className="text-slate-400">
                Additional financial intelligence tools
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
