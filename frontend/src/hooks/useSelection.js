import { useMemo, useState } from "react";

// Handles selected publications and visible pagination
export const useSelection = (filteredPublications) => {
  const [selectedPublications, setSelectedPublications] = useState([]);
  const [visibleCount, setVisibleCount] = useState(6);

  const visiblePublications = useMemo(
    () => (filteredPublications || []).slice(0, visibleCount),
    [filteredPublications, visibleCount]
  );

  const handlePublicationSelect = (pubId) => {
    setSelectedPublications((prev) =>
      prev.includes(pubId)
        ? prev.filter((id) => id !== pubId)
        : [...prev, pubId]
    );
  };

  const handleSelectAll = () => {
    const visible = visiblePublications;
    const visibleIds = visible.map((pub) => pub.id);
    const allVisibleSelected = visibleIds.every((id) =>
      selectedPublications.includes(id)
    );
    if (allVisibleSelected) {
      setSelectedPublications((prev) =>
        prev.filter((id) => !visibleIds.includes(id))
      );
    } else {
      setSelectedPublications((prev) =>
        Array.from(new Set([...prev, ...visibleIds]))
      );
    }
  };

  const clearSelection = () => setSelectedPublications([]);

  return {
    selectedPublications,
    setSelectedPublications,
    visibleCount,
    setVisibleCount,
    visiblePublications,
    handlePublicationSelect,
    handleSelectAll,
    clearSelection,
  };
};

export default useSelection;
