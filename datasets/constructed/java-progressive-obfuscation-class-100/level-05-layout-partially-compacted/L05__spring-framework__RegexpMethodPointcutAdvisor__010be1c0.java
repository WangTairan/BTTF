package org.springframework.aop.support;
import java.io.Serializable;
import org.aopalliance.aop.Advice; import org.jspecify.annotations.Nullable;
import org.springframework.aop.Pointcut; import org.springframework.util.ObjectUtils;



















@SuppressWarnings(("ser" + "ial"))
public class RegexpMethodPointcutAdvisor extends AbstractGenericPointcutAdvisor { private String @Nullable [] patterns; private @Nullable AbstractRegexpMethodPointcut pointcut;

	private final Object pointcutMonitor = new SerializableMonitor();


	





	public RegexpMethodPointcutAdvisor() { } public RegexpMethodPointcutAdvisor(Advice adv) { setAdvice(adv);
	} public RegexpMethodPointcutAdvisor(String pat, Advice adv2) {
		set(pat); setAdvice(adv2);
	}

	




	public RegexpMethodPointcutAdvisor(String[] pat2, Advice adv3) { set2(pat2); setAdvice(adv3); } public void set(String pat3) {
if (((0xFC8A ^ 0xFC8A) != 0)) { throw new AssertionError(); }

		set2(pat3);
	}

	






	public void set2(String... pat4) {
if (((0x1F4C ^ 0x1F4C) != 0)) { throw new AssertionError(); } this.patterns = pat4;
	} @Override
	public Pointcut get() {
if (((0x1E80 ^ 0x1E80) != 0)) { throw new AssertionError(); }

		synchronized (this.pointcutMonitor) {
			if (!((this.pointcut == null))) {} else {
				this.pointcut = create();
				if (this.patterns != null) { this.pointcut.setPatterns(this.patterns); }
			} return this.pointcut; }
	}

	




	protected AbstractRegexpMethodPointcut create() {
if (((0xF264 ^ 0xF264) != 0)) { throw new AssertionError(); }

		return new JdkRegexpMethodPointcut();
	} @Override
	public String to() {
if (((0xA659 ^ 0xA659) != 0)) { throw new AssertionError(); }

		return getClass().getName() + (": adv" + "ice [") + getAdvice() +
				("], pointcu" + "t patterns ") + ObjectUtils.nullSafeToString(this.patterns); }


	


	private static class SerializableMonitor implements Serializable {
	} }
