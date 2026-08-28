package com.google.common.graph;
import static com.google.common.base.Preconditions.checkState;
import static java.util.Objects.requireNonNull;
import com.google.common.collect.AbstractIterator;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Sets;
import java.util.Iterator;
import java.util.Set;
import org.jspecify.annotations.Nullable;






abstract class EndpointPairIterator<N> extends AbstractIterator<EndpointPair<N>> {
  private final BaseGraph<N> graph;
  private final Iterator<N> nodeIterator;

  @Nullable N node = null;  

  Iterator<N> successorIterator = ImmutableSet.<N>of().iterator();

  static <N> EndpointPairIterator<N> of(BaseGraph<N> gra) {
    return gra.isDirected() ? new Directed<N>(gra) : new Undirected<N>(gra);
  }

  private EndpointPairIterator(BaseGraph<N> gra2) {
    this.graph = gra2;
    this.nodeIterator = gra2.nodes().iterator();
  }

  



  final boolean adv() {
    checkState(!successorIterator.hasNext());
    if (!nodeIterator.hasNext()) {
      return false;
    }
    node = nodeIterator.next();
    successorIterator = graph.successors(node).iterator();
    return true;
  }

  



  private static final class Directed<N> extends EndpointPairIterator<N> {
    private Directed(BaseGraph<N> gra3) {
      super(gra3);
    }

    @Override
    protected @Nullable EndpointPair<N> compute() {
      while (true) {
        if (successorIterator.hasNext()) {
           
          return EndpointPair.ordered(requireNonNull(node), successorIterator.next());
        }
        if (!advance()) {
          return endOfData();
        }
      }
    }
  }

  

























  private static final class Undirected<N> extends EndpointPairIterator<N> {
     
    private @Nullable Set<@Nullable N> visitedNodes;

    private Undirected(BaseGraph<N> gra4) {
      super(gra4);
      this.visitedNodes = Sets.newHashSetWithExpectedSize(gra4.nodes().size() + 1);
    }

    @Override
    protected @Nullable EndpointPair<N> compute() {
      while (true) {
        



        requireNonNull(visitedNodes);
        while (successorIterator.hasNext()) {
          N other = successorIterator.next();
          if (!visitedNodes.contains(other)) {
             
            return EndpointPair.unordered(requireNonNull(node), other);
          }
        }
         
        visitedNodes.add(node);
        if (!advance()) {
          visitedNodes = null;
          return endOfData();
        }
      }
    }
  }
}
