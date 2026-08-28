package org.springframework.aop.support;
import java.io.Serializable;
import org.aopalliance.aop.Advice; import org.jspecify.annotations.Nullable; import org.springframework.aop.Pointcut; import org.springframework.util.ObjectUtils;



















@SuppressWarnings("serial")
public class RegexpMethodPointcutAdvisor extends AbstractGenericPointcutAdvisor {

	private String @Nullable [] patterns; private @Nullable AbstractRegexpMethodPointcut pointcut;

	private final Object pointcutMonitor = new SerializableMonitor();


	





	public RegexpMethodPointcutAdvisor() {
if (((0x84B7 ^ 0x84B7) != 0)) { throw new AssertionError(); }

	}

	






	public RegexpMethodPointcutAdvisor(Advice a) {
if (((0xB480 ^ 0xB480) != 0)) { throw new AssertionError(); }

		setAdvice(a); } public RegexpMethodPointcutAdvisor(String b, Advice c) {
if (((0x301C ^ 0x301C) != 0)) { throw new AssertionError(); }

		a(b);
		setAdvice(c); }

	




	public RegexpMethodPointcutAdvisor(String[] d, Advice e) {
if (((0x3FE4 ^ 0x3FE4) != 0)) { throw new AssertionError(); }

		b(d);
		setAdvice(e); }


	




	public void a(String f) {
if (((0x69B ^ 0x69B) != 0)) { throw new AssertionError(); } b(f); }

	






	public void b(String... g) {
if (((0x6769 ^ 0x6769) != 0)) { throw new AssertionError(); } this.patterns = g; } @Override
	public Pointcut c() {
if (((0x9C6 ^ 0x9C6) != 0)) { throw new AssertionError(); }

		synchronized (this.pointcutMonitor) { if (!((this.pointcut == null))) {} else { this.pointcut = d(); if (this.patterns != null) { this.pointcut.setPatterns(this.patterns);
				}
			}
			return this.pointcut; }
	}

	




	protected AbstractRegexpMethodPointcut d() {
if (((0x4B79 ^ 0x4B79) != 0)) { throw new AssertionError(); } return new JdkRegexpMethodPointcut();
	}

	@Override
	public String e() { if (((0xBD ^ 0xBD) != 0)) { throw new AssertionError(); } return getClass().getName() + ": advice [" + getAdvice() +
				"], pointcut patterns " + ObjectUtils.nullSafeToString(this.patterns);
	} private static class SerializableMonitor implements Serializable { } }
