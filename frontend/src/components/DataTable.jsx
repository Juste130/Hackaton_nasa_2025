import React, { useMemo, useState } from "react";
import "./DataTable.css";

const DataTable = ({
  publications,
  selectedPublications,
  onPublicationSelect,
}) => {
  const [sortField, setSortField] = useState("date");
  const [sortDirection, setSortDirection] = useState("desc");
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const sortedPublications = useMemo(() => {
    const sorted = [...publications].sort((a, b) => {
      let aValue, bValue;

      switch (sortField) {
        case "title":
          aValue = a.title.toLowerCase();
          bValue = b.title.toLowerCase();
          break;
        case "authors":
          aValue = a.authors[0].toLowerCase();
          bValue = b.authors[0].toLowerCase();
          break;
        case "date":
          aValue = new Date(a.date);
          bValue = new Date(b.date);
          break;

        default:
          aValue = a[sortField];
          bValue = b[sortField];
      }

      if (aValue < bValue) return sortDirection === "asc" ? -1 : 1;
      if (aValue > bValue) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [publications, sortField, sortDirection]);

  const paginatedPublications = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return sortedPublications.slice(startIndex, startIndex + itemsPerPage);
  }, [sortedPublications, currentPage]);

  const totalPages = Math.ceil(sortedPublications.length / itemsPerPage);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
    setCurrentPage(1);
  };

  const SortIcon = ({ field }) => {
    if (sortField !== field) return "↕️";
    return sortDirection === "asc" ? "↑" : "↓";
  };

  return (
    <div className="data-table">
      <div className="table-header">
        <h3>Publications Table</h3>
        <p>Advanced view with sorting and pagination</p>
      </div>

      <div className="table-container">
        <table className="publications-table">
          <thead>
            <tr>
              <th>
                <input
                  type="checkbox"
                  checked={
                    publications.length > 0 &&
                    selectedPublications.length === publications.length
                  }
                  onChange={() => {
                    if (selectedPublications.length === publications.length) {
                      publications.forEach((pub) =>
                        onPublicationSelect(pub.id)
                      );
                    } else {
                      publications.forEach((pub) =>
                        onPublicationSelect(pub.id)
                      );
                    }
                  }}
                />
              </th>
              <th onClick={() => handleSort("title")} className="sortable">
                Title{" "}
                <span className="sort-icon">
                  <SortIcon field="title" />
                </span>
              </th>
              <th onClick={() => handleSort("authors")} className="sortable">
                Authors{" "}
                <span className="sort-icon">
                  <SortIcon field="authors" />
                </span>
              </th>
              <th onClick={() => handleSort("date")} className="sortable">
                Date{" "}
                <span className="sort-icon">
                  <SortIcon field="date" />
                </span>
              </th>
              <th>Organisms</th>
              <th>Phenomena</th>
            </tr>
          </thead>
          <tbody>
            {paginatedPublications.map((publication) => (
              <tr
                key={publication.id}
                className={
                  selectedPublications.includes(publication.id)
                    ? "selected"
                    : ""
                }
              >
                <td>
                  <input
                    type="checkbox"
                    checked={selectedPublications.includes(publication.id)}
                    onChange={() => onPublicationSelect(publication.id)}
                  />
                </td>
                <td className="title-cell">
                  <div className="title-content">
                    <strong>{publication.title}</strong>
                    <span className="journal">{publication.journal}</span>
                  </div>
                </td>
                <td>
                  <div className="authors-list">
                    {publication.authors.slice(0, 2).join(", ")}
                    {publication.authors.length > 2 && " et al."}
                  </div>
                </td>
                <td>{new Date(publication.date).toLocaleDateString()}</td>
                <td>
                  <div className="tags-list">
                    {publication.organisms.map((org) => (
                      <span key={org} className="tag organism">
                        {org}
                      </span>
                    ))}
                  </div>
                </td>
                <td>
                  <div className="tags-list">
                    {publication.phenomena.map((phen) => (
                      <span key={phen} className="tag phenomenon">
                        {phen}
                      </span>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="table-pagination">
          <button
            className="pagination-btn"
            disabled={currentPage === 1}
            onClick={() => setCurrentPage(currentPage - 1)}
          >
            Previous
          </button>

          <span className="pagination-info">
            Page {currentPage} of {totalPages}
          </span>

          <button
            className="pagination-btn"
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage(currentPage + 1)}
          >
            Next
          </button>
        </div>
      )}

      <div className="table-footer">
        <p>
          Showing {paginatedPublications.length} of {sortedPublications.length}{" "}
          publications
        </p>
      </div>
    </div>
  );
};

export default DataTable;
