import { useState } from "react";
import graphApiService from "../services/graphApi";

// Encapsulates graph data fetching and state
export const useGraphData = () => {
  const [graphData, setGraphData] = useState(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [graphError, setGraphError] = useState(null);

  const run = async (fn) => {
    setGraphLoading(true);
    setGraphError(null);
    try {
      const data = await fn();
      setGraphData(data);
    } catch (err) {
      setGraphError(err.message);
      console.error("Graph error:", err);
    } finally {
      setGraphLoading(false);
    }
  };

  const search = async (params) =>
    run(() => graphApiService.searchGraph(params));
  const filter = async (params) =>
    run(() => graphApiService.filterGraph(params));
  const loadFull = async (params = { limit: 100 }) =>
    run(() => graphApiService.getFullGraph(params));
  const clear = () => {
    setGraphData(null);
    setGraphError(null);
  };

  return {
    graphData,
    graphLoading,
    graphError,
    search,
    filter,
    loadFull,
    clear,
    dismissError: () => setGraphError(null),
  };
};

export default useGraphData;
