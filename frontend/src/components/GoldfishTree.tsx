import React, { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
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

export const GoldfishTree: React.FC<GoldfishTreeProps> = ({
  nodes,
  selectedNodeId,
  onSelectNode,
}) => {
  const { flowNodes, flowEdges } = useMemo(() => {
    const positions = layoutTree(nodes);

    const flowNodes: Node[] = nodes.map((n) => ({
      id: String(n.id),
      position: positions.get(n.id) || { x: 0, y: 0 },
      data: {
        label: n.turn_number ? `T${n.turn_number}: ${n.label}` : n.label,
      },
      style: {
        border: `2px solid ${n.id === selectedNodeId ? "#6366f1" : "#1e293b"}`,
        background: n.id === selectedNodeId ? "#312e81" : "#0f172a",
        color: "#f1f5f9",
        borderRadius: 12,
        padding: 8,
        width: NODE_WIDTH - 20,
        fontSize: 13,
      },
    }));

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
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#1e293b" gap={24} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
};
