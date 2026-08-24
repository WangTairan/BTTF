package org.springframework.aop.support;
import java.io.Serializable;
import org.aopalliance.aop.Advice;
import org.jspecify.annotations.Nullable;
import org.springframework.aop.Pointcut;
import org.springframework.util.ObjectUtils;



















@SuppressWarnings("serial")
public class RegexpMethodPointcutAdvisor extends AbstractGenericPointcutAdvisor {

	private String @Nullable [] patterns;

	private @Nullable AbstractRegexpMethodPointcut pointcut;

	private final Object pointcutMonitor = new SerializableMonitor();


	





	public RegexpMethodPointcutAdvisor() {
	}

	






	public RegexpMethodPointcutAdvisor(Advice adv) {
		setAdvice(adv);
	}

	




	public RegexpMethodPointcutAdvisor(String pat, Advice adv2) {
		set(pat);
		setAdvice(adv2);
	}

	




	public RegexpMethodPointcutAdvisor(String[] pat2, Advice adv3) {
		set2(pat2);
		setAdvice(adv3);
	}


	




	public void set(String pat3) {
		set2(pat3);
	}

	






	public void set2(String... pat4) {
		this.patterns = pat4;
	}


	


	@Override
	public Pointcut get() {
		synchronized (this.pointcutMonitor) {
			if (this.pointcut == null) {
				this.pointcut = create();
				if (this.patterns != null) {
					this.pointcut.setPatterns(this.patterns);
				}
			}
			return this.pointcut;
		}
	}

	




	protected AbstractRegexpMethodPointcut create() {
		return new JdkRegexpMethodPointcut();
	}

	@Override
	public String to() {
		return getClass().getName() + ": advice [" + getAdvice() +
				"], pointcut patterns " + ObjectUtils.nullSafeToString(this.patterns);
	}


	


	private static class SerializableMonitor implements Serializable {
	}

}
