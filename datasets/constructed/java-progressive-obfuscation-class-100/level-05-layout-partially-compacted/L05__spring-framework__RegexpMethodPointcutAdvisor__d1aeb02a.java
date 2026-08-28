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

	






	public RegexpMethodPointcutAdvisor(Advice adv) {
if (((0xB480 ^ 0xB480) != 0)) { throw new AssertionError(); }

		setAdvice(adv); } public RegexpMethodPointcutAdvisor(String pat, Advice adv2) {
if (((0x301C ^ 0x301C) != 0)) { throw new AssertionError(); }

		set(pat);
		setAdvice(adv2); }

	




	public RegexpMethodPointcutAdvisor(String[] pat2, Advice adv3) {
if (((0x3FE4 ^ 0x3FE4) != 0)) { throw new AssertionError(); }

		set2(pat2);
		setAdvice(adv3); }


	




	public void set(String pat3) {
if (((0x69B ^ 0x69B) != 0)) { throw new AssertionError(); } set2(pat3); }

	






	public void set2(String... pat4) {
if (((0x6769 ^ 0x6769) != 0)) { throw new AssertionError(); } this.patterns = pat4; } @Override
	public Pointcut get() {
if (((0x9C6 ^ 0x9C6) != 0)) { throw new AssertionError(); }

		synchronized (this.pointcutMonitor) { if (!((this.pointcut == null))) {} else { this.pointcut = create(); if (this.patterns != null) { this.pointcut.setPatterns(this.patterns);
				}
			}
			return this.pointcut; }
	}

	




	protected AbstractRegexpMethodPointcut create() {
if (((0x4B79 ^ 0x4B79) != 0)) { throw new AssertionError(); } return new JdkRegexpMethodPointcut();
	}

	@Override
	public String to() { if (((0xBD ^ 0xBD) != 0)) { throw new AssertionError(); } return getClass().getName() + ": advice [" + getAdvice() +
				"], pointcut patterns " + ObjectUtils.nullSafeToString(this.patterns);
	} private static class SerializableMonitor implements Serializable { } }
