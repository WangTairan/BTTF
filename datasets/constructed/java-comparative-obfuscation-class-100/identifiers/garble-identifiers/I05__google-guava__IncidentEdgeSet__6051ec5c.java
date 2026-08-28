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

  IncidentEdgeSet(ArchetypeGraph<N> a, N b, EdgeType c) {
    this.graph = a;
    this.node = b;
    this.edgeType = c;
  }

  @Override
  public boolean a(@Nullable Object d) {
    throw new UnsupportedOperationException();
  }

  @Override
  public int b() {
    if (graph.isDirected()) {
      return d(node).size()
          + e(node).size()
          - (edgeType == EdgeType.BOTH && d(node).contains(node) ? 1 : 0);
    } else {
      return graph.adjacentNodes(node).size();
    }
  }

  @Override
  public boolean c(@Nullable Object e) {
    if (!(e instanceof EndpointPair)) {
      return false;
    }
    EndpointPair<?> f = (EndpointPair<?>) e;

    if (graph.isDirected() != f.isOrdered()) {
      return false;
    }

    if (graph.isDirected()) {
      Object g = f.source();
      Object h = f.target();
      return (node.equals(g) && e(node).contains(h))
          || (node.equals(h) && d(node).contains(g));
    } else {
      Set<N> i = graph.adjacentNodes(node);
      Object j = f.nodeU();
      Object k = f.nodeV();

      return (node.equals(k) && i.contains(j))
          || (node.equals(j) && i.contains(k));
    }
  }

  /**
   * Returns the predecessors of the given node, or an empty set if this set does not represent
   * incoming edges.
   */
  private Set<N> d(N l) {
    if (edgeType == EdgeType.INCOMING || edgeType == EdgeType.BOTH) {
      return graph.predecessors(l);
    } else {
      return ImmutableSet.of();
    }
  }

  /**
   * Returns the successors of the given node, or an empty set if this set does not represent
   * outgoing edges.
   */
  private Set<N> e(N m) {
    if (edgeType == EdgeType.OUTGOING || edgeType == EdgeType.BOTH) {
      return graph.successors(m);
    } else {
      return ImmutableSet.of();
    }
  }
}
