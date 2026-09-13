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
              The same habit of testing the first answer instead of trusting
              it shaped Jacob&rsquo;s finance work at Emory University&rsquo;s
              Goizueta Business School. In one academic valuation exercise
              &mdash; not a client engagement &mdash; an initial Comcast
              model produced a value of $57.11 per share. Rather than
              treating a precise output as a correct one, Jacob reconsidered
              the peer group, replaced media-heavy comparables with
              businesses that better reflected Comcast&rsquo;s connectivity
              economics, normalized beta from 0.655 to 1.00, and revised the
              margin and capital-expenditure assumptions. The resulting
              range, $29.75 to $35.74, was less dramatic and more defensible.
              The same discipline applies to automation work: a polished
              model, dashboard, or AI response is not evidence by itself
              &mdash; the underlying data, assumptions, and controls have to
              make sense.
            </p>
            <p>
              Jacob was also a student fund analyst with Blue Eagle Capital,
              an Emory student-managed investment fund, where he developed
              investment memos and pitch decks, presented recommendations to
              the investment committee for review, and monitored approved
              positions against thesis-specific KPIs and catalysts. That
              experience reinforced a second principle behind EchoFrame: the
              work does not end when a recommendation is presented &mdash;
              someone has to remain accountable for whether it performs as
              expected and for recognizing when the facts change.
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
