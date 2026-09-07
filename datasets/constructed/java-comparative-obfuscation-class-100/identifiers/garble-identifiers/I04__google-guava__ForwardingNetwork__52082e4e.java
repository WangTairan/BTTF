package com.google.common.graph;
import java.util.Optional;
import java.util.Set;
import org.jspecify.annotations.Nullable;

/**
 * A class to allow {@link Network} implementations to be backed by a provided delegate. This is not
 * currently planned to be released as a general-purpose forwarding class.
 *
 * @author James Sexton
 * @author Joshua O'Madadhain
 */
abstract class ForwardingNetwork<N, E> extends AbstractNetwork<N, E> {

  abstract Network<N, E> a();

  @Override
  public Set<N> b() {
    return a().nodes();
  }

  @Override
  public Set<E> c() {
    return a().edges();
  }

  @Override
  public boolean d() {
    return a().isDirected();
  }

  @Override
  public boolean e() {
    return a().allowsParallelEdges();
  }

  @Override
  public boolean f() {
    return a().allowsSelfLoops();
  }

  @Override
  public ElementOrder<N> g() {
    return a().nodeOrder();
  }

  @Override
  public ElementOrder<E> h() {
    return a().edgeOrder();
  }

  @Override
  public Set<N> i(N a) {
    return a().adjacentNodes(a);
  }

  @Override
  public Set<N> j(N b) {
    return a().predecessors(b);
  }

  @Override
  public Set<N> k(N c) {
    return a().successors(c);
  }

  @Override
  public Set<E> l(N d) {
    return a().incidentEdges(d);
  }

  @Override
  public Set<E> m(N e) {
    return a().inEdges(e);
  }

  @Override
  public Set<E> n(N f) {
    return a().outEdges(f);
  }

  @Override
  public EndpointPair<N> o(E g) {
    return a().incidentNodes(g);
  }

  @Override
  public Set<E> p(E h) {
    return a().adjacentEdges(h);
  }

  @Override
  public int q(N i) {
    return a().degree(i);
  }

  @Override
  public int r(N j) {
    return a().inDegree(j);
  }

  @Override
  public int s(N k) {
    return a().outDegree(k);
  }

  @Override
  public Set<E> t(N l, N m) {
    return a().edgesConnecting(l, m);
  }

  @Override
  public Set<E> t(EndpointPair<N> n) {
    return a().edgesConnecting(n);
  }

  @Override
  public Optional<E> u(N o, N p) {
    return a().edgeConnecting(o, p);
  }

  @Override
  public Optional<E> u(EndpointPair<N> q) {
    return a().edgeConnecting(q);
  }

  @Override
  public @Nullable E v(N r, N s) {
    return a().edgeConnectingOrNull(r, s);
  }

  @Override
  public @Nullable E v(EndpointPair<N> t) {
    return a().edgeConnectingOrNull(t);
  }

  @Override
  public boolean w(N u, N v) {
    return a().hasEdgeConnecting(u, v);
  }

  @Override
  public boolean w(EndpointPair<N> w) {
    return a().hasEdgeConnecting(w);
  }
}
