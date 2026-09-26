# Code readability model papers

This file records a selective reading list for code-readability baselines and
competitors. Local PDF copies, when available, live in the ignored
`bib/local_papers/` directory and are not part of the public repository.

## Locally retained papers

- `BuseWeimer_2010_LearningMetricCodeReadability.pdf` — original learned readability metric; classic baseline with surface/code features.
- `PosnettHindleDevanbu_2011_SimplerModelSoftwareReadability.pdf` — sparse readability model using size/entropy-style metrics; important simple baseline.
- `DornWeimer_2012_GeneralSoftwareReadabilityModel.pdf` — general readability model with visual/spatial/linguistic features; important cross-language baseline.
- `SergeyukEtAl_2024_ReassessingJavaCodeReadabilityModels.pdf` — ICPC/JetBrains human-centered reassessment of Java readability models; directly relevant to the JetBrains dataset.
- `VitaleEtAl_2025_PersonalizedCodeReadabilityAssessment.pdf` — ICPC 2025 personalized/LLM readability assessment negative result; useful for positioning and threats to validity.

## Important papers not downloaded here

These are relevant competitor/model papers, but I did not save PDFs because the publisher/metadata sources mark them as closed or returned 403 during download. They should still be cited/read if we have institutional access.

- Scalabrino et al. 2018, "A Comprehensive Model for Code Readability", Journal of Software: Evolution and Process, DOI: `10.1002/smr.1958`.
- Scalabrino et al. 2016, "Improving Code Readability Models with Textual Features", ICPC, DOI: `10.1109/ICPC.2016.7503707`.
- Mi et al. 2018, "Improving Code Readability Classification Using Convolutional Neural Networks", Information and Software Technology, DOI: `10.1016/j.infsof.2018.07.006`.
- Mi et al. 2021, "The Effectiveness of Data Augmentation in Code Readability Classification", Information and Software Technology, DOI: `10.1016/j.infsof.2020.106378`.
- Mi et al. 2022, "Towards Using Visual, Semantic and Structural Features to Improve Code Readability Classification", Journal of Systems and Software, DOI: `10.1016/j.jss.2022.111454`.
- Mi et al. 2023, "A Graph-Based Code Representation Method to Improve Code Readability Classification", Empirical Software Engineering, DOI: `10.1007/s10664-023-10319-6`.
- Mi et al. 2025, "Towards Explainable Code Readability Classification With Graph Neural Networks", Journal of Software: Evolution and Process, DOI: `10.1002/smr.70048`.

## Considered but not included as primary competitor PDFs

- Mi et al. 2018, "An Inception Architecture-Based Model for Improving Code Readability Classification" — conference precursor to the stronger 2018 DeepCRM journal paper.
- Fakhoury et al. 2019, "Improving Source Code Readability: Theory and Practice" — relevant motivation paper about readability-improvement commits, but not a direct leaderboard classifier; public preprint links were unavailable/timeout during download.
- Vitale et al. 2023, "Using Deep Learning to Automatically Improve Code Readability" — generation/refactoring method rather than a readability scoring competitor.
