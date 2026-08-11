// About page — Stitch about_deceptiscan design (Protocol & Mission)
// Static informational page, no API calls.
// NOTE: The "faux terminal / stats block" (SYSTEM INTEGRITY 100%, ENCRYPTION AES-256,
// LOG RETENTION ZERO) is verbatim from the Stitch source — the comment in code.html
// explicitly labels it a cosmetic "faux terminal." It is not fetched from any backend
// and does not imply a real metrics endpoint. Retained as-is per design integrity rule.

import React from 'react';

const About: React.FC = () => {
  return (
    <main className="flex-grow relative bg-lead-charcoal">
      {/* Hero Section */}
      <section className="relative pt-24 pb-32 px-margin-mobile md:px-margin-desktop border-b border-outline-variant/30 overflow-hidden">
        <div className="absolute inset-0 grid-overlay pointer-events-none" />
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: 'linear-gradient(to bottom, transparent 0%, rgba(143, 48, 42, 0.1) 50%, transparent 100%)',
            animation: 'about-scan 4s linear infinite',
          }}
        />
        <div className="max-w-container-max mx-auto relative z-10">
          <div className="flex flex-col gap-4 max-w-3xl">
            <span className="font-metadata-xs text-metadata-xs text-ink-red uppercase tracking-widest border border-ink-red/30 self-start px-2 py-1 bg-ink-red/5">
              DOC. REF: ABT-001
            </span>
            <h1 className="font-display-lg text-display-lg text-primary uppercase leading-none">
              PROTOCOL &<br />MISSION
            </h1>
            <p className="font-technical-sm text-technical-sm text-on-surface-variant max-w-xl mt-6 border-l-2 border-ink-red pl-4">
              INITIATING BRIEFING... Establishing the foundational directives and operational parameters of the DeceptiScan information forensics apparatus.
            </p>
          </div>
        </div>
        <style>{`
          @keyframes about-scan {
            0% { transform: translateY(-100%); }
            100% { transform: translateY(100%); }
          }
        `}</style>
      </section>

      {/* Main Content */}
      <section className="max-w-container-max mx-auto px-margin-mobile md:px-margin-desktop -mt-16 relative z-20 pb-24">

        {/* Philosophy Block */}
        <div className="bg-carbon-gray border border-outline-variant shadow-[0_24px_60px_rgba(0,0,0,0.5)] flex flex-col md:flex-row mb-16">
          <div className="p-8 md:p-12 flex-1 relative flex flex-col justify-center">
            <div className="absolute left-0 top-0 bottom-0 w-8 bg-surface-container-low border-r border-outline-variant/50 flex flex-col pt-12 items-center text-outline-variant font-technical-sm text-technical-sm opacity-50 space-y-2 select-none hidden sm:flex">
              <span>01</span><span>02</span><span>03</span><span>04</span>
              <span>05</span><span>06</span><span>07</span><span>08</span>
            </div>
            <div className="sm:pl-8">
              <h2 className="font-headline-lg text-headline-lg text-primary mb-6 flex items-center gap-3">
                <span className="material-symbols-outlined text-ink-red">gavel</span>
                EVIDENCE OVER VIBES.
              </h2>
              <div className="space-y-4 text-on-surface-variant font-body-md text-body-md">
                <p>
                  In an era saturated with synthetic narratives and weaponized ambiguity, intuition is obsolete. DeceptiScan was engineered to dismantle the noise and isolate the empirical facts. We do not deal in sentiment; we process data.
                </p>
                <p>
                  Our architecture is designed for deep investigation. We treat every claim as a suspect, subjecting it to rigorous cross-referencing, metadata extraction, and logical consistency checks. The result is a cold, calculated assessment of truth.
                </p>
              </div>
            </div>
          </div>
          <div className="w-full md:w-1/3 min-h-[300px] border-l border-outline-variant relative overflow-hidden bg-surface-container-highest">
            <div
              className="absolute inset-0 bg-cover bg-center grayscale opacity-80 mix-blend-luminosity"
              style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuCd0x9DjY9gY5pLQLJVcIR7BfYOK4_eN8FcplLS8yh6cMXwxCOdlEmymKe3FpC5rLKzkz7jphQY40Rf8Wh_0S-DbWf7qoOHaEILabLGmW84oRLJ1aRIbyblaFWjtJY008EfVyogfG00dd-K8zd5cnNUfAVv2saS5Zb_kDGxYyIRIJQ3Ae-Jmu_H-8JjWhCM0ZhnocmemWd_4hHpyQ1Qho6hIN2ANV-xVmYP30Mz07eqK-lIC-DIYjIvmA')" }}
            />
            <div
              className="absolute inset-0 mix-blend-overlay pointer-events-none"
              style={{ backgroundImage: "url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0IiBoZWlnaHQ9IjQiPgo8cmVjdCB3aWR0aD0iNCIgaGVpZ2h0PSI0IiBmaWxsPSJ0cmFuc3BhcmVudCIvPgo8Y2lyY2xlIGN4PSIxIiBjeT0iMSIgcj0iMSIgZmlsbD0icmdiYSgyNTUsIDI1NSwgMjU1LCAwLjA1KSIvPgo8L3N2Zz4=')" }}
            />
          </div>
        </div>

        {/* Methodology Grid */}
        <div className="mb-16">
          <div className="flex items-center gap-4 mb-8">
            <h3 className="font-label-caps text-label-caps text-primary border border-outline-variant px-3 py-1 bg-surface-container-low uppercase">
              OPERATIONAL METHODOLOGY
            </h3>
            <div className="h-px bg-outline-variant flex-grow" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-surface-container-low border border-outline-variant p-6 hover:border-ink-red transition-colors group relative overflow-hidden">
              <div className="absolute top-0 right-0 bg-surface-variant text-on-surface-variant font-metadata-xs text-metadata-xs px-2 py-1 border-b border-l border-outline-variant group-hover:bg-ink-red group-hover:text-white transition-colors">
                PHASE 01
              </div>
              <span className="material-symbols-outlined text-4xl text-outline-variant mb-4 group-hover:text-primary transition-colors block">manage_search</span>
              <h4 className="font-headline-lg-mobile text-headline-lg-mobile text-primary mb-2">EXTRACTION</h4>
              <p className="font-technical-sm text-technical-sm text-on-surface-variant">
                Target inputs are parsed to isolate declarative statements, discarding rhetorical noise. Entities, timestamps, and contextual anchors are categorized into an immutable evidence schema.
              </p>
            </div>
            <div className="bg-surface-container-low border border-outline-variant p-6 hover:border-ink-red transition-colors group relative overflow-hidden">
              <div className="absolute top-0 right-0 bg-surface-variant text-on-surface-variant font-metadata-xs text-metadata-xs px-2 py-1 border-b border-l border-outline-variant group-hover:bg-ink-red group-hover:text-white transition-colors">
                PHASE 02
              </div>
              <span className="material-symbols-outlined text-4xl text-outline-variant mb-4 group-hover:text-primary transition-colors block">account_tree</span>
              <h4 className="font-headline-lg-mobile text-headline-lg-mobile text-primary mb-2">CORRELATION</h4>
              <p className="font-technical-sm text-technical-sm text-on-surface-variant">
                Extracted claims are mapped against primary sources, vetted archives, and authoritative indices. Discrepancies are flagged; corroborations are logged with cryptographic verification.
              </p>
            </div>
            <div className="bg-surface-container-low border border-outline-variant p-6 hover:border-ink-red transition-colors group relative overflow-hidden">
              <div className="absolute top-0 right-0 bg-surface-variant text-on-surface-variant font-metadata-xs text-metadata-xs px-2 py-1 border-b border-l border-outline-variant group-hover:bg-ink-red group-hover:text-white transition-colors">
                PHASE 03
              </div>
              <span className="material-symbols-outlined text-4xl text-outline-variant mb-4 group-hover:text-primary transition-colors block">fact_check</span>
              <h4 className="font-headline-lg-mobile text-headline-lg-mobile text-primary mb-2">ADJUDICATION</h4>
              <p className="font-technical-sm text-technical-sm text-on-surface-variant">
                A final Confidence Score is synthesized based on source reliability, contradiction frequency, and metadata integrity. The resulting Investigator File is sealed for review.
              </p>
            </div>
          </div>
        </div>

        {/* Transparency / Security Protocol */}
        <div className="border border-outline-variant bg-surface relative">
          <div className="absolute -top-8 left-0 border-t border-l border-r border-outline-variant bg-surface px-4 py-1 flex items-center gap-2">
            <span className="material-symbols-outlined text-sm text-outline-variant">folder_open</span>
            <span className="font-label-caps text-label-caps text-on-surface-variant">FILE: SECURITY_PROTOCOL</span>
          </div>
          <div className="p-8 flex flex-col lg:flex-row gap-8 items-start">
            <div className="flex-1">
              <h3 className="font-stamp-lg text-stamp-lg text-ink-red mb-4 uppercase opacity-80 border-b border-outline-variant/30 pb-2 inline-block">
                TRANSPARENCY DIRECTIVE
              </h3>
              <div className="font-technical-sm text-technical-sm text-on-surface-variant space-y-4 max-w-2xl">
                <p>
                  Investigations require secrecy; systemic trust requires transparency. The <span className="text-primary font-bold">Investigator File</span> protocol ensures that every determination made by DeceptiScan leaves a transparent audit trail.
                </p>
                <p>
                  <strong>DATA PRIVACY:</strong> When logged in, your analyses are saved to your account and accessible in your Case Archive. Anonymous submissions are processed for your active session without being linked to any account history.
                </p>
              </div>
            </div>
            {/* Illustrative forensic telemetry block — updated to state true system details */}
            <div className="bg-carbon-gray border border-outline-variant p-4 w-full lg:w-72 font-metadata-xs text-metadata-xs text-verification-green">
              <div className="flex justify-between border-b border-outline-variant/50 pb-2 mb-2">
                <span>ANALYSIS ENGINE</span>
                <span>DISTILBERT</span>
              </div>
              <div className="flex justify-between border-b border-outline-variant/50 pb-2 mb-2">
                <span>CLASSIFIER</span>
                <span>NLP SEQUENCE</span>
              </div>
              <div className="flex justify-between border-b border-outline-variant/50 pb-2 mb-2">
                <span>SYSTEM STATUS</span>
                <span>ONLINE</span>
              </div>
              <div className="mt-4 text-outline-variant animate-pulse">
                &gt; AWAITING FURTHER INSTRUCTION_
              </div>
            </div>
          </div>
        </div>

      </section>
    </main>
  );
};

export default About;
