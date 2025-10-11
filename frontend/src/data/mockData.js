export const publications = [
  {
    id: 1,
    title: "Effects of Microgravity on Human Bone Density",
    authors: ["Smith, J.", "Johnson, A.", "Williams, R."],
    abstract: "This study examines the significant loss of bone density in astronauts during long-duration space missions and potential countermeasures.",
    date: "2023-03-15",
    journal: "Space Medicine Journal",
    organisms: ["Human"],
    phenomena: ["Microgravity"],
    systems: ["Skeletal"],
    mission: "ISS",
    citations: 42
  },
  {
    id: 2,
    title: "Plant Growth in Lunar Soil Simulant",
    authors: ["Chen, L.", "Rodriguez, M.", "Tanaka, K."],
    abstract: "Research on Arabidopsis thaliana growth in simulated lunar regolith, showing promising results for future lunar agriculture.",
    date: "2024-01-10",
    journal: "Astrobiology",
    organisms: ["Plants"],
    phenomena: ["Radiation", "Soil Composition"],
    systems: ["Growth", "Metabolism"],
    mission: "Artemis",
    citations: 28
  },
  {
    id: 3,
    title: "Immune System Response to Space Radiation",
    authors: ["Garcia, P.", "Lee, S.", "Nowak, T."],
    abstract: "Comprehensive analysis of cosmic radiation effects on immune cell function and potential protective compounds.",
    date: "2023-11-30",
    journal: "Immunology in Space",
    organisms: ["Human", "Mouse"],
    phenomena: ["Radiation"],
    systems: ["Immune"],
    mission: "ISS",
    citations: 35
  }
];

export const filters = {
  organisms: ["Human", "Mouse", "Plants", "Cells", "Microorganisms"],
  phenomena: ["Microgravity", "Radiation", "Confinement", "Isolation"],
  systems: ["Skeletal", "Muscular", "Immune", "Neurological", "Cardiovascular"],
  missions: ["ISS", "Artemis", "Apollo", "Shuttle", "Gateway"]
};