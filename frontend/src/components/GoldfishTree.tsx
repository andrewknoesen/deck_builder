import React, { useEffect, useMemo } from "react";
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  useReactFlow,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { GoldfishNode } from "../types/goldfish";

const NODE_WIDTH = 220;
const LEVEL_HEIGHT = 110;

function layoutTree(nodes: GoldfishNode[]): Map<number, { x: number; y: number }> {
  const childrenByParent = new Map<number | null, GoldfishNode[]>();
  nodes.forEach((n) => {
    const key = n.parent_id;
    if (!childrenByParent.has(key)) childrenByParent.set(key, []);
    childrenByParent.get(key)!.push(n);
  });
  childrenByParent.forEach((list) => list.sort((a, b) => a.order_index - b.order_index));

  const positions = new Map<number, { x: number; y: number }>();
  let nextX = 0;

  function place(node: GoldfishNode, depth: number): number {
    const children = childrenByParent.get(node.id) || [];
    let x: number;
    if (children.length === 0) {
      x = nextX;
      nextX += NODE_WIDTH;
    } else {
      const childXs = children.map((c) => place(c, depth + 1));
      x = (childXs[0] + childXs[childXs.length - 1]) / 2;
    }
    positions.set(node.id, { x, y: depth * LEVEL_HEIGHT });
    return x;
  }

  const roots = childrenByParent.get(null) || [];
  roots.forEach((root) => place(root, 0));

  return positions;
}

interface GoldfishTreeProps {
  nodes: GoldfishNode[];
  selectedNodeId: number | null;
  onSelectNode: (id: number) => void;
}

const GoldfishTreeInner: React.FC<GoldfishTreeProps> = ({
  nodes,
  selectedNodeId,
  onSelectNode,
}) => {
  const { fitView } = useReactFlow();

  // ReactFlow's `fitView` prop only frames the graph on first mount. Every
  // action you take while goldfishing adds a node, so without this the tree
  // panel freezes on whatever the first one or two nodes looked like and
  // never shows where you actually are - the whole point of a branch tree
  // you navigate by clicking nodes. Re-fit whenever the node count changes.
  useEffect(() => {
    fitView({ padding: 0.3, duration: 300, maxZoom: 1.1 });
  }, [nodes.length, fitView]);

  const { flowNodes, flowEdges } = useMemo(() => {
    const positions = layoutTree(nodes);

    const flowNodes: Node[] = nodes.map((n) => {
      const trackerSummary =
        n.trackers && Object.keys(n.trackers).length > 0
          ? Object.entries(n.trackers)
              .map(([name, value]) => `${name}: ${value}`)
              .join(" · ")
          : null;

      // Skip the "T{n}:" prefix when the label already says "Turn N" (the
      // next_turn action's own auto-generated label) - avoids "T1: Turn 1".
      const needsTurnPrefix = n.turn_number && !/^Turn \d+/.test(n.label);
      const label = `${needsTurnPrefix ? `T${n.turn_number}: ` : ""}${n.label}${
        trackerSummary ? `\n${trackerSummary}` : ""
      }`;

      return {
        id: String(n.id),
        position: positions.get(n.id) || { x: 0, y: 0 },
        data: { label },
        style: {
          border: `2px solid ${n.id === selectedNodeId ? "#ecaa0b" : "#2f271e"}`,
          background: n.id === selectedNodeId ? "#462600" : "#1b150e",
          color: "#f3ede7",
          borderRadius: 12,
          padding: 8,
          width: NODE_WIDTH - 20,
          fontSize: 13,
          whiteSpace: "pre-line" as const,
        },
      };
    });

    const flowEdges: Edge[] = nodes
      .filter((n) => n.parent_id !== null)
      .map((n) => ({
        id: `e-${n.parent_id}-${n.id}`,
        source: String(n.parent_id),
        target: String(n.id),
        style: { stroke: "#334155" },
      }));

    return { flowNodes, flowEdges };
  }, [nodes, selectedNodeId]);

  return (
    <div style={{ width: "100%", height: "100%" }}>
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        onNodeClick={(_, node) => onSelectNode(Number(node.id))}
        fitView
        fitViewOptions={{ padding: 0.3, maxZoom: 1.1 }}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#2f271e" gap={24} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
};

export const GoldfishTree: React.FC<GoldfishTreeProps> = (props) => (
  <ReactFlowProvider>
    <GoldfishTreeInner {...props} />
  </ReactFlowProvider>
);
