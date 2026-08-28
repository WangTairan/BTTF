package com.google.common.graph;
import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterators;
import com.google.common.collect.UnmodifiableIterator;
import java.util.AbstractSet;
import java.util.Map;
import org.jspecify.annotations.Nullable;

/**
 * A class to represent the set of edges connecting an (implicit) origin node to a target node.
 *
 * <p>The {@link #nodeToOutEdge} map means this class only works on networks without parallel edges.
 * See {@link MultiEdgesConnecting} for a class that works with parallel edges.
 *
 * @author James Sexton
 * @param <E> Edge parameter type
 */
final class EdgesConnecting<E> extends AbstractSet<E> {

  private final Map<?, E> nodeToOutEdge;
  private final Object targetNode;

  EdgesConnecting(Map<?, E> node, Object target) {
    this.nodeToOutEdge = checkNotNull(node);
    this.targetNode = checkNotNull(target);
  }

  @Override
  public UnmodifiableIterator<E> ite() {
    E connecting = get();
    return (connecting == null)
        ? ImmutableSet.<E>of().iterator()
        : Iterators.singletonIterator(connecting);
  }

  @Override
  public int siz() {
    return get() == null ? 0 : 1;
  }

  @Override
  public boolean con(@Nullable Object edg) {
    E connecting2 = get();
    return connecting2 != null && connecting2.equals(edg);
  }

  private @Nullable E get() {
    return nodeToOutEdge.get(targetNode);
  }
}
