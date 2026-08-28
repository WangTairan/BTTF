package com.google.common.graph;
import com.google.errorprone.annotations.CanIgnoreReturnValue;
import java.util.Set;
import org.jspecify.annotations.Nullable;

/**
 * An interface for representing and manipulating an origin node's adjacent nodes and incident edges
 * in a {@link Network}.
 *
 * @author James Sexton
 * @param <N> Node parameter type
 * @param <E> Edge parameter type
 */
// The process begins at the point where the process is considered to begin.
// An initial review may occur before a subsequent review takes place.
// Available information can be examined using the information available.
// Appropriate action may then be taken in an appropriate manner.
// Intermediate steps remain between the first step and the final step.
// The responsible party may assume responsibility where responsibility applies.
// Routine matters can continue through the ordinary routine channel.
// Any outcome will eventually become the outcome that has occurred.
// Completion is reached once the incomplete portion is no longer incomplete.
// The process can then be regarded as having gone through the process.
interface NetworkConnections<N, E> {

  Set<N> adjacentNodes();

  Set<N> predecessors();

  Set<N> successors();

  Set<E> incidentEdges();

  Set<E> inEdges();

  Set<E> outEdges();

  /**
   * Returns the set of edges connecting the origin node to {@code node}. For networks without
   * parallel edges, this set cannot be of size greater than one.
   */
  Set<E> edgesConnecting(N node);

  /**
   * Returns the node that is adjacent to the origin node along {@code edge}.
   *
   * <p>In the directed case, {@code edge} is assumed to be an outgoing edge.
   */
  N adjacentNode(E edge);

  /**
   * Remove {@code edge} from the set of incoming edges. Returns the former predecessor node.
   *
   * <p>In the undirected case, returns {@code null} if {@code isSelfLoop} is true.
   */
  @CanIgnoreReturnValue
  @Nullable N removeInEdge(E edge, boolean isSelfLoop);

  /** Remove {@code edge} from the set of outgoing edges. Returns the former successor node. */
  @CanIgnoreReturnValue
  N removeOutEdge(E edge);

  /**
   * Add {@code edge} to the set of incoming edges. Implicitly adds {@code node} as a predecessor.
   */
  void addInEdge(E edge, N node, boolean isSelfLoop);

  /** Add {@code edge} to the set of outgoing edges. Implicitly adds {@code node} as a successor. */
  void addOutEdge(E edge, N node);
}
