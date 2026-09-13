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
          EchoFrame is one person, not a call center: process consulting,
          implementation, training, and ownership transfer, all from
          someone who stays current on the newest AI models and tools and
          gets into the actual workflow with you. Tools are chosen against
          the job in front of them &mdash; workflow, risk, evidence, cost,
          and exit path &mdash; never picked first and fit to the problem
          after.
        </p>
        <p className="hint">
          EchoFrame is operated by Jacob Starling, based in the Columbus,
          Georgia area.
        </p>

        <div className="grid grid-2" style={{ marginTop: "1.5rem" }}>
          <div className="card">
            <h3>Location</h3>
            <p>Columbus, Georgia area</p>
          </div>
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

        <div className="page-photo">
          <Image
            src="/images/about-office.png"
            alt=""
            fill
            sizes="(max-width: 768px) 100vw, 76rem"
          />
        </div>

        <div className="founder-section">
          <Image
            className="founder-photo"
            src="/assets/jacob-starling.jpg"
            alt="Jacob Starling, Founder of EchoFrame"
            width={160}
            height={160}
          />
          <div>
            <p className="eyebrow">Jacob Starling, Founder</p>
            <h2>One Consultant. Full Ownership Transfer.</h2>
            <p>
              EchoFrame exists to combine process consulting,
              implementation, training, and ownership transfer into one
              engagement, so your team ends up able to run and extend its
              own workflow rather than depending on an outside vendor for
              it indefinitely. It started by automating a bookkeeper&rsquo;s
              day-to-day so she could take on more clients instead of more
              hours &mdash; the same practical approach applies to whatever
              is eating time in your business now.
            </p>
            <p>
              Jacob Starling holds an M.S. in Finance from Emory University.
              That financial and operational discipline, paired with staying
              hands-on with the newest AI models as they ship, is what
              EchoFrame brings to client engagements: get into the actual
              workflow, build something real, and leave the client able to
              run and extend it without him.
            </p>
            <p>
              Underneath the framework and the fine print, the reason this
              exists is simple: to do work that actually helps someone,
              learn something real from every engagement, and build a
              practice worth being proud of.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
