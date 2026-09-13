import type { Metadata } from "next";
import Image from "next/image";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "About",
  description:
    "EchoFrame is one consultant who builds practical AI and automation for small businesses, then trains the team to run it. Vendor-neutral: tools are chosen against the workflow, not the other way around.",
};

export default function AboutPage() {
  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs trail={[{ href: "/about", label: "About" }]} />
        <p className="eyebrow">Point of View</p>
        <h1>The Case for Capability Over Dependency.</h1>
        <p>
          I&rsquo;m one person, not a call center: process consulting,
          implementation, training, and ownership transfer, all from
          someone who stays current on the newest AI models and tools and
          gets into the actual workflow with you. I choose tools against
          the job in front of them &mdash; workflow, risk, evidence, cost,
          and exit path &mdash; never picked first and fit to the problem
          after.
        </p>

        <div className="founder-section">
          <Image
            className="founder-photo"
            src="/assets/jacob-starling.jpg"
            alt="Jacob Starling, Founder of EchoFrame"
            width={320}
            height={320}
          />
          <div>
            <p className="eyebrow">Jacob Starling, Founder</p>
            <h2>One Consultant. Full Ownership Transfer.</h2>
            <p>
              EchoFrame exists to combine process consulting,
              implementation, training, and ownership transfer into one
              engagement, so your team ends up able to run and extend its
              own workflow rather than depending on an outside vendor for
              it indefinitely. I started by automating a bookkeeper&rsquo;s
              day-to-day so she could take on more clients instead of more
              hours &mdash; the same practical approach applies to
              whatever is eating time in your business now.
            </p>
            <p>
              That practical approach is backed by my M.S. in Finance from
              Emory University&rsquo;s Goizueta Business School, where the
              habit of testing an answer instead of trusting it was the
              whole discipline. In one academic valuation exercise &mdash;
              not client work &mdash; an initial model I built produced a
              precise-looking share price; reconsidering the peer group
              and key assumptions produced a very different, more
              defensible range. As a student fund analyst with Blue Eagle
              Capital, an Emory student-managed fund, I developed
              investment memos, presented recommendations to the
              investment committee for review, and monitored positions
              against thesis-specific KPIs. Both experiences point to the
              same principle behind EchoFrame: a polished model or AI
              output is not evidence by itself, and the work isn&rsquo;t
              done when a recommendation is made &mdash; someone has to
              stay accountable for whether it holds up.
            </p>
            <p>
              Underneath the framework and the fine print, the reason this
              exists is simple: I want to do work that actually helps
              someone, learn something real from every engagement, and
              build a practice worth being proud of.
            </p>
          </div>
        </div>

        <p className="hint">EchoFrame is operated by Jacob Starling.</p>

        <div style={{ marginTop: "1.5rem" }}>
          <div className="card">
            <h3>Contact</h3>
            <p>
              <a href="tel:+17063661096">(706) 366-1096</a>
              <br />
              <a href="mailto:jacob.starling@echoframe.net">
                jacob.starling@echoframe.net
              </a>
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
