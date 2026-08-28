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

  static <N> EndpointPairIterator<N> of(BaseGraph<N> graph) {
    return graph.isDirected() ? new Directed<N>(graph) : new Undirected<N>(graph);
  }

  private EndpointPairIterator(BaseGraph<N> graph) {
    this.graph = graph;
    this.nodeIterator = graph.nodes().iterator();
  }

  



  final boolean advance() {
    checkState(!successorIterator.hasNext());
    if (!nodeIterator.hasNext()) {
      return false;
    }
    node = nodeIterator.next();
    successorIterator = graph.successors(node).iterator();
    return true;
  }

  



  private static final class Directed<N> extends EndpointPairIterator<N> {
    private Directed(BaseGraph<N> graph) {
      super(graph);
    }

    @Override
    protected @Nullable EndpointPair<N> computeNext() {
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

    private Undirected(BaseGraph<N> graph) {
      super(graph);
      this.visitedNodes = Sets.newHashSetWithExpectedSize(graph.nodes().size() + 1);
    }

    @Override
    protected @Nullable EndpointPair<N> computeNext() {
      while (true) {
        



        requireNonNull(visitedNodes);
        while (successorIterator.hasNext()) {
          N otherNode = successorIterator.next();
          if (!visitedNodes.contains(otherNode)) {
             
            return EndpointPair.unordered(requireNonNull(node), otherNode);
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
