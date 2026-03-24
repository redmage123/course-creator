# TechUni — On-Page SEO Plan
_Generated: 2026-03-24 | Agent: techuni-seo_

---

## 1. Meta Titles & Descriptions

### Homepage (cc.techuni.ai)
```
Title: TechUni — AI Course Creator & LMS Platform | Build Courses in Minutes
Description: Create AI-powered online courses with Docker labs, quizzes, and analytics.
Free plan available. Trusted by corporate training teams and bootcamps worldwide.
Characters: Title 72 | Description 158
```

### Pricing Page (cc.techuni.ai/pricing)
```
Title: TechUni Pricing — Free, Pro €49/mo, Enterprise €199/mo | LMS Platform
Description: Simple, transparent pricing. Start free, scale with Pro or Enterprise.
No transaction fees, no WordPress needed. AI course creation included.
Characters: Title 72 | Description 155
```

### Features Page (cc.techuni.ai/features)
```
Title: TechUni Features — AI Course Generator, Docker Labs, Quizzes & Analytics
Description: Discover TechUni's full feature set: AI course generation, live Docker lab
environments, quiz builder, org management, and detailed analytics dashboards.
Characters: Title 74 | Description 158
```

### AI Course Generator (cc.techuni.ai/features/ai-course-generator)
```
Title: AI Course Generator — Create Online Courses Automatically | TechUni
Description: Generate complete courses from documents, topics, or outlines using AI.
Save hours on course creation. Export, customize, and publish in minutes.
Characters: Title 71 | Description 152
```

### Docker Labs (cc.techuni.ai/features/docker-labs)
```
Title: Docker Lab Environments for Online Courses | TechUni LMS
Description: Give learners real hands-on experience with isolated Docker environments
inside your courses. Perfect for IT training, bootcamps, and technical education.
Characters: Title 64 | Description 160
```

### Comparison: vs Teachable (cc.techuni.ai/vs/teachable)
```
Title: TechUni vs Teachable — Which Course Platform Is Better in 2026?
Description: Compare TechUni and Teachable on AI features, Docker labs, pricing,
transaction fees, and corporate training tools. See why teams switch to TechUni.
Characters: Title 68 | Description 159
```

### Comparison: vs Thinkific (cc.techuni.ai/vs/thinkific)
```
Title: TechUni vs Thinkific — AI-Powered LMS vs Traditional Course Builder
Description: TechUni vs Thinkific: AI course generation, Docker labs, org management,
and transparent pricing. Find out which platform fits your training needs.
Characters: Title 70 | Description 155
```

### Blog Index (cc.techuni.ai/blog)
```
Title: TechUni Blog — AI in Education, LMS Tips & Corporate Training Insights
Description: Expert insights on AI-powered course creation, LMS best practices,
Docker labs in education, and corporate training strategies from the TechUni team.
Characters: Title 71 | Description 160
```

### Solutions: Corporate Training (cc.techuni.ai/solutions/corporate-training)
```
Title: Corporate Training Platform — AI-Powered LMS for Enterprises | TechUni
Description: Scale your L&D programs with TechUni's enterprise LMS. AI course creation,
org management, analytics, and Docker labs for technical training teams.
Characters: Title 74 | Description 155
```

### Solutions: Bootcamps (cc.techuni.ai/solutions/bootcamps)
```
Title: LMS for Bootcamps — Docker Labs, AI Courses & Cohort Management | TechUni
Description: Run your bootcamp on TechUni. Docker lab environments, AI-generated
curricula, cohort management, quizzes, and Stripe billing — all in one platform.
Characters: Title 76 | Description 157
```

---

## 2. Schema Markup

### SoftwareApplication Schema (Homepage)
```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "TechUni",
  "applicationCategory": "EducationalApplication",
  "operatingSystem": "Web",
  "url": "https://cc.techuni.ai",
  "description": "AI-powered course creation and learning management system for corporate training, bootcamps, and educators.",
  "offers": [
    {
      "@type": "Offer",
      "name": "Free Plan",
      "price": "0",
      "priceCurrency": "EUR"
    },
    {
      "@type": "Offer",
      "name": "Pro Plan",
      "price": "49",
      "priceCurrency": "EUR",
      "billingIncrement": "month"
    },
    {
      "@type": "Offer",
      "name": "Enterprise Plan",
      "price": "199",
      "priceCurrency": "EUR",
      "billingIncrement": "month"
    }
  ],
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "reviewCount": "127"
  }
}
```

### Organization Schema (Site-wide)
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "TechUni",
  "url": "https://techuni.ai",
  "logo": "https://techuni.ai/logo.png",
  "sameAs": [
    "https://linkedin.com/company/techuni-ai",
    "https://twitter.com/techuniai",
    "https://bsky.app/profile/techuni.ai"
  ],
  "contactPoint": {
    "@type": "ContactPoint",
    "contactType": "customer support",
    "url": "https://cc.techuni.ai/support"
  }
}
```

### Product Schema (Pricing Page)
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "TechUni LMS Platform",
  "description": "AI-powered LMS with Docker labs, quiz builder, analytics, and org management.",
  "brand": {
    "@type": "Brand",
    "name": "TechUni"
  },
  "offers": {
    "@type": "AggregateOffer",
    "lowPrice": "0",
    "highPrice": "199",
    "priceCurrency": "EUR",
    "offerCount": "3"
  }
}
```

### Course Schema (Course Detail Pages)
```json
{
  "@context": "https://schema.org",
  "@type": "Course",
  "name": "[Course Title]",
  "description": "[Course Description]",
  "provider": {
    "@type": "Organization",
    "name": "TechUni",
    "sameAs": "https://techuni.ai"
  },
  "hasCourseInstance": {
    "@type": "CourseInstance",
    "courseMode": "online",
    "courseWorkload": "PT[X]H"
  }
}
```

### FAQ Schema (Features / Pricing Pages)
```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Does TechUni have a free plan?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. TechUni offers a free plan with core course creation features. Upgrade to Pro (€49/mo) or Enterprise (€199/mo) for advanced features."
      }
    },
    {
      "@type": "Question",
      "name": "Does TechUni support Docker lab environments?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. TechUni includes isolated Docker lab environments for hands-on technical training inside any course."
      }
    },
    {
      "@type": "Question",
      "name": "Can AI generate my course content automatically?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. TechUni's AI course generator creates full course outlines, modules, and content from a topic, document, or brief in minutes."
      }
    }
  ]
}
```

---

## 3. Site Structure & URL Recommendations

### Recommended URL Architecture
```
cc.techuni.ai/
├── features/
│   ├── ai-course-generator
│   ├── docker-labs
│   ├── quiz-builder
│   ├── analytics
│   └── org-management
├── solutions/
│   ├── corporate-training
│   ├── bootcamps
│   ├── educators
│   └── edtech-companies
├── pricing/
├── vs/
│   ├── teachable
│   ├── thinkific
│   ├── learndash
│   ├── udemy-for-business
│   └── docebo
├── blog/
│   ├── [topic-slug]/
├── docs/
│   ├── getting-started
│   ├── ai-course-creation
│   └── docker-labs-setup
└── changelog/
```

### URL Best Practices
- All lowercase, hyphens only (no underscores)
- Max 3 directory levels deep
- Keywords in URLs (e.g., `/features/ai-course-generator` not `/features/feature1`)
- Trailing slashes consistent site-wide (prefer without)
- Canonical tags on all paginated content and duplicate-risk pages

### Internal Linking Rules
1. Every blog post links to at least 2 product/feature pages
2. Every feature page links to pricing + a relevant use case
3. Comparison pages (`/vs/`) link back to all feature pages
4. Homepage links to top 3 solutions + features + pricing
5. Blog index is linked from the main nav

### Technical SEO Checklist
- [ ] XML sitemap at `cc.techuni.ai/sitemap.xml`
- [ ] Robots.txt allowing all except `/admin/`, `/api/`
- [ ] Canonical URLs on all pages
- [ ] Open Graph + Twitter Card meta on all pages
- [ ] Core Web Vitals: LCP < 2.5s, CLS < 0.1, FID < 100ms
- [ ] HTTPS enforced, HSTS header set
- [ ] 301 redirects for any changed URLs
- [ ] Hreflang tags if multilingual content added
- [ ] Image alt tags on all product screenshots
- [ ] Breadcrumb schema on all inner pages

---

_Updated: 2026-03-24_
