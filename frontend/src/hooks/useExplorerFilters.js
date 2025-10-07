import { useEffect, useMemo, useState } from "react";

// Manages search, dynamic filters, year range, and filtered list
export const useExplorerFilters = ({
  publications,
  currentYear,
  minYear,
  maxYear,
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFilters, setSelectedFilters] = useState({
    organisms: [],
    phenomena: [],
    systems: [],
    missions: [],
    yearRange: [currentYear, currentYear],
  });

  useEffect(() => {
    // Initialize when min/max are known
    setSelectedFilters((prev) => ({
      ...prev,
      yearRange: [minYear, maxYear],
    }));
  }, [minYear, maxYear]);

  const filteredPublications = useMemo(() => {
    let results = publications || [];

    // Text search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      results = results.filter(
        (pub) =>
          pub.title.toLowerCase().includes(query) ||
          pub.abstract.toLowerCase().includes(query) ||
          pub.authors.some((a) => a.toLowerCase().includes(query)) ||
          pub.journal.toLowerCase().includes(query)
      );
    }

    // Category filters
    Object.keys(selectedFilters).forEach((key) => {
      if (key !== "yearRange" && selectedFilters[key].length > 0) {
        results = results.filter((pub) =>
          selectedFilters[key].some((filter) => pub[key]?.includes(filter))
        );
      }
    });

    // Year range
    results = results.filter((pub) => {
      const pubYear = new Date(pub.date).getFullYear();
      return (
        pubYear >= selectedFilters.yearRange[0] &&
        pubYear <= selectedFilters.yearRange[1]
      );
    });

    return results;
  }, [publications, searchQuery, selectedFilters]);

  const handleFilterToggle = (category, value) => {
    setSelectedFilters((prev) => {
      const newFilters = { ...prev };
      if (newFilters[category].includes(value)) {
        newFilters[category] = newFilters[category].filter(
          (item) => item !== value
        );
      } else {
        newFilters[category] = [...newFilters[category], value];
      }
      return newFilters;
    });
  };

  const handleYearRangeChange = (newRange) => {
    setSelectedFilters((prev) => ({ ...prev, yearRange: newRange }));
  };

  const clearAllFilters = () => {
    setSelectedFilters({
      organisms: [],
      phenomena: [],
      systems: [],
      missions: [],
      yearRange: [minYear, currentYear],
    });
    setSearchQuery("");
  };

  return {
    searchQuery,
    setSearchQuery,
    selectedFilters,
    setSelectedFilters,
    filteredPublications,
    handleFilterToggle,
    handleYearRangeChange,
    clearAllFilters,
  };
};

export default useExplorerFilters;
