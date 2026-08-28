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

	






	public RegexpMethodPointcutAdvisor(Advice advice) {
		setAdvice(advice);
	}

	




	public RegexpMethodPointcutAdvisor(String pattern, Advice advice) {
		setPattern(pattern);
		setAdvice(advice);
	}

	




	public RegexpMethodPointcutAdvisor(String[] patterns, Advice advice) {
		setPatterns(patterns);
		setAdvice(advice);
	}


	




	public void setPattern(String pattern) {
		setPatterns(pattern);
	}

	






	public void setPatterns(String... patterns) {
		this.patterns = patterns;
	}


	


	@Override
	public Pointcut getPointcut() {
		synchronized (this.pointcutMonitor) {
			if (this.pointcut == null) {
				this.pointcut = createPointcut();
				if (this.patterns != null) {
					this.pointcut.setPatterns(this.patterns);
				}
			}
			return this.pointcut;
		}
	}

	




	protected AbstractRegexpMethodPointcut createPointcut() {
		return new JdkRegexpMethodPointcut();
	}

	@Override
	public String toString() {
		return getClass().getName() + ": advice [" + getAdvice() +
				"], pointcut patterns " + ObjectUtils.nullSafeToString(this.patterns);
	}


	


	private static class SerializableMonitor implements Serializable {
	}

}
