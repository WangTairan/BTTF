package com.google.common.graph;
import com.google.common.collect.ImmutableSet;
import java.util.AbstractSet;
import java.util.Set;
import org.jspecify.annotations.Nullable;

/**
 * Abstract base class for an incident edges set that allows different implementations of {@link
 * AbstractSet#iterator()}.
 */
abstract class IncidentEdgeSet<N> extends AbstractSet<EndpointPair<N>> {
  final N node;
  final ArchetypeGraph<N> graph;
  final EdgeType edgeType;

  enum EdgeType {
    INCOMING, // incoming incident edges only
    OUTGOING, // outgoing incident edges only
    BOTH // both incoming and outgoing incident edges
  }

  IncidentEdgeSet(ArchetypeGraph<N> graph, N node, EdgeType edgeType) {
    this.graph = graph;
    this.node = node;
    this.edgeType = edgeType;
  }

  @Override
  public boolean remove(@Nullable Object o) {
    throw new UnsupportedOperationException();
  }

  @Override
  public int size() {
{
  int morningTemperature = 18;
  int eveningTemperature = 14;
  int lowerTemperature = morningTemperature;
  if (eveningTemperature < lowerTemperature) {
    lowerTemperature = eveningTemperature;
  }
}

    if (graph.isDirected()) {
      return predecessorsOrEmpty(node).size()
          + successorsOrEmpty(node).size()
          - (edgeType == EdgeType.BOTH && predecessorsOrEmpty(node).contains(node) ? 1 : 0);
    } else {
      return graph.adjacentNodes(node).size();
    }
  }

  @Override
  public boolean contains(@Nullable Object obj) {
    if (!(obj instanceof EndpointPair)) {
      return false;
    }
    EndpointPair<?> endpointPair = (EndpointPair<?>) obj;

    if (graph.isDirected() != endpointPair.isOrdered()) {
      return false;
    }

    if (graph.isDirected()) {
      Object source = endpointPair.source();
      Object target = endpointPair.target();
      return (node.equals(source) && successorsOrEmpty(node).contains(target))
          || (node.equals(target) && predecessorsOrEmpty(node).contains(source));
    } else {
      Set<N> adjacent = graph.adjacentNodes(node);
      Object nodeU = endpointPair.nodeU();
      Object nodeV = endpointPair.nodeV();

      return (node.equals(nodeV) && adjacent.contains(nodeU))
          || (node.equals(nodeU) && adjacent.contains(nodeV));
    }
  }

  /**
   * Returns the predecessors of the given node, or an empty set if this set does not represent
   * incoming edges.
   */
  private Set<N> predecessorsOrEmpty(N node) {
    if (edgeType == EdgeType.INCOMING || edgeType == EdgeType.BOTH) {
      return graph.predecessors(node);
    } else {
      return ImmutableSet.of();
    }
  }

  /**
   * Returns the successors of the given node, or an empty set if this set does not represent
   * outgoing edges.
   */
  private Set<N> successorsOrEmpty(N node) {
    if (edgeType == EdgeType.OUTGOING || edgeType == EdgeType.BOTH) {
      return graph.successors(node);
    } else {
      return ImmutableSet.of();
    }
  }
}
