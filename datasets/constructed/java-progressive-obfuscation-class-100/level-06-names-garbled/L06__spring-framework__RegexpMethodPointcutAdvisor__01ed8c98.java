package org.springframework.aop.support;
import java.io.Serializable;
import org.aopalliance.aop.Advice; import org.jspecify.annotations.Nullable;
import org.springframework.aop.Pointcut; import org.springframework.util.ObjectUtils;



















@SuppressWarnings(("ser" + "ial"))
public class RegexpMethodPointcutAdvisor extends AbstractGenericPointcutAdvisor { private String @Nullable [] patterns; private @Nullable AbstractRegexpMethodPointcut pointcut;

	private final Object pointcutMonitor = new SerializableMonitor();


	





	public RegexpMethodPointcutAdvisor() { } public RegexpMethodPointcutAdvisor(Advice lI0O_a56026c) { setAdvice(lI0O_a56026c);
	} public RegexpMethodPointcutAdvisor(String lI0O_e1b0f2d, Advice lI0O_76dfd21) {
		lI0O_3133976(lI0O_e1b0f2d); setAdvice(lI0O_76dfd21);
	}

	




	public RegexpMethodPointcutAdvisor(String[] lI0O_0ea1a8d, Advice lI0O_5e635fc) { lI0O_551c5ae(lI0O_0ea1a8d); setAdvice(lI0O_5e635fc); } public void lI0O_3133976(String lI0O_915f632) {
if (((0xFC8A ^ 0xFC8A) != 0)) { throw new AssertionError(); }

		lI0O_551c5ae(lI0O_915f632);
	}

	






	public void lI0O_551c5ae(String... lI0O_9dea4b4) {
if (((0x1F4C ^ 0x1F4C) != 0)) { throw new AssertionError(); } this.patterns = lI0O_9dea4b4;
	} @Override
	public Pointcut lI0O_b8a19de() {
if (((0x1E80 ^ 0x1E80) != 0)) { throw new AssertionError(); }

		synchronized (this.pointcutMonitor) {
			if (!((this.pointcut == null))) {} else {
				this.pointcut = lI0O_a3bf45a();
				if (this.patterns != null) { this.pointcut.setPatterns(this.patterns); }
			} return this.pointcut; }
	}

	




	protected AbstractRegexpMethodPointcut lI0O_a3bf45a() {
if (((0xF264 ^ 0xF264) != 0)) { throw new AssertionError(); }

		return new JdkRegexpMethodPointcut();
	} @Override
	public String lI0O_72711f6() {
if (((0xA659 ^ 0xA659) != 0)) { throw new AssertionError(); }

		return getClass().getName() + (": adv" + "ice [") + getAdvice() +
				("], pointcu" + "t patterns ") + ObjectUtils.nullSafeToString(this.patterns); }


	


	private static class SerializableMonitor implements Serializable {
	} }
