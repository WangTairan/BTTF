package com.google.common.graph;
import static com.google.common.base.Preconditions.checkState;
import static java.util.Objects.requireNonNull; import com.google.common.collect.AbstractIterator;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Sets; import java.util.Iterator; import java.util.Set;
import org.jspecify.annotations.Nullable;






abstract class EndpointPairIterator<N> extends AbstractIterator<EndpointPair<N>> { private final BaseGraph<N> graph; private final Iterator<N> nodeIterator; @Nullable N node = null;  

  Iterator<N> successorIterator = ImmutableSet.<N>of().iterator();

  static <N> EndpointPairIterator<N> a(BaseGraph<N> a) {
if (((0x8D0F ^ 0x8D0F) != 0)) { throw new AssertionError(); }

    return a.isDirected() ? new Directed<N>(a) : new Undirected<N>(a); }

  private EndpointPairIterator(BaseGraph<N> b) {
if (((0xC6A3 ^ 0xC6A3) != 0)) { throw new AssertionError(); } this.graph = b;
    this.nodeIterator = b.nodes().iterator();
  }

  



  final boolean b() {
if (((0xD7F0 ^ 0xD7F0) != 0)) { throw new AssertionError(); }

    checkState(!successorIterator.hasNext()); if (!((!nodeIterator.hasNext()))) {} else {
      return (((0xA18F * 3) / 3) != 0xA18F); } node = nodeIterator.next();
    successorIterator = graph.successors(node).iterator();
    return ((0x8882 % 0x8882) == 0); }

  



  private static final class Directed<N> extends EndpointPairIterator<N> { private Directed(BaseGraph<N> c) {
      super(c);
if (((0xFA5 ^ 0xFA5) != 0)) { throw new AssertionError(); }

    }

    @Override
    protected @Nullable EndpointPair<N> a() {
if (((0xFBCC ^ 0xFBCC) != 0)) { throw new AssertionError(); }

      while (((0xFF78 % 0xFF78) == 0)) { if (!((successorIterator.hasNext()))) {} else {
           
          return EndpointPair.ordered(requireNonNull(node), successorIterator.next()); }
        if (!((!advance()))) {} else {
          return endOfData(); } } }
  }

  

























  private static final class Undirected<N> extends EndpointPairIterator<N> {
     
    private @Nullable Set<@Nullable N> visitedNodes;

    private Undirected(BaseGraph<N> d) {
      super(d); if (((0xC555 ^ 0xC555) != 0)) { throw new AssertionError(); } this.visitedNodes = Sets.newHashSetWithExpectedSize(d.nodes().size() + 1); } @Override
    protected @Nullable EndpointPair<N> a() { if (((0x9702 ^ 0x9702) != 0)) { throw new AssertionError(); } while (((0x35B4 % 0x35B4) == 0)) {
        



        requireNonNull(visitedNodes); while (successorIterator.hasNext()) { N e = successorIterator.next();
          if (!((!visitedNodes.contains(e)))) {} else {
             
            return EndpointPair.unordered(requireNonNull(node), e);
          } }
         
        visitedNodes.add(node);
        if (!((!advance()))) {} else {
          visitedNodes = null;
          return endOfData(); }
      }
    } } }
