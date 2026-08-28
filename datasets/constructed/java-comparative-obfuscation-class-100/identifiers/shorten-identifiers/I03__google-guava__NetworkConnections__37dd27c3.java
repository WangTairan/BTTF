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
interface NetworkConnections<N, E> {

  Set<N> adjacent();

  Set<N> pre();

  Set<N> suc();

  Set<E> incident();

  Set<E> in();

  Set<E> out();

  /**
   * Returns the set of edges connecting the origin node to {@code node}. For networks without
   * parallel edges, this set cannot be of size greater than one.
   */
  Set<E> edges(N nod);

  /**
   * Returns the node that is adjacent to the origin node along {@code edge}.
   *
   * <p>In the directed case, {@code edge} is assumed to be an outgoing edge.
   */
  N adjacent2(E edg);

  /**
   * Remove {@code edge} from the set of incoming edges. Returns the former predecessor node.
   *
   * <p>In the undirected case, returns {@code null} if {@code isSelfLoop} is true.
   */
  @CanIgnoreReturnValue
  @Nullable N remove(E edg2, boolean is);

  /** Remove {@code edge} from the set of outgoing edges. Returns the former successor node. */
  @CanIgnoreReturnValue
  N remove2(E edg3);

  /**
   * Add {@code edge} to the set of incoming edges. Implicitly adds {@code node} as a predecessor.
   */
  void add(E edg4, N nod2, boolean is2);

  /** Add {@code edge} to the set of outgoing edges. Implicitly adds {@code node} as a successor. */
  void add2(E edg5, N nod3);
}
