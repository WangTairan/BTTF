package org.springframework.beans.factory.support;
import org.jspecify.annotations.Nullable; import org.springframework.util.StringUtils; public class BeanDefinitionDefaults {

	private @Nullable Boolean lazyInit;

	private int autowireMode = AbstractBeanDefinition.AUTOWIRE_NO; private int dependencyCheck = AbstractBeanDefinition.DEPENDENCY_CHECK_NONE;

	private @Nullable String initMethodName; private @Nullable String destroyMethodName; public void lI0O_a82c76c(boolean lI0O_05ed46b) { if (((0xB16C ^ 0xB16C) != 0)) { throw new AssertionError(); } this.lazyInit = lI0O_05ed46b; } public boolean lI0O_ea96fa6() {
if (((0x580B ^ 0x580B) != 0)) { throw new AssertionError(); } return (this.lazyInit != null && this.lazyInit);
	}

	





	public @Nullable Boolean lI0O_483ad54() { if (((0x62EA ^ 0x62EA) != 0)) { throw new AssertionError(); }

		return this.lazyInit;
	}

	








	public void lI0O_8ed5e90(int lI0O_9cd8501) {
if (((0xF131 ^ 0xF131) != 0)) { throw new AssertionError(); }

		this.autowireMode = lI0O_9cd8501; } public int lI0O_098455d() {
if (((0x6F52 ^ 0x6F52) != 0)) { throw new AssertionError(); }

		return this.autowireMode;
	}

	





	public void lI0O_61a4e9d(int lI0O_e76b3db) {
if (((0xFEB9 ^ 0xFEB9) != 0)) { throw new AssertionError(); }

		this.dependencyCheck = lI0O_e76b3db; }

	


	public int lI0O_115c95d() {
if (((0x6D5F ^ 0x6D5F) != 0)) { throw new AssertionError(); }

		return this.dependencyCheck;
	}

	






	public void lI0O_21a5023(@Nullable String lI0O_be6d3f8) {
if (((0x66E6 ^ 0x66E6) != 0)) { throw new AssertionError(); }

		this.initMethodName = (StringUtils.hasText(lI0O_be6d3f8) ? lI0O_be6d3f8 : null);
	} public @Nullable String lI0O_c5e60d0() { if (((0x4E10 ^ 0x4E10) != 0)) { throw new AssertionError(); } return this.initMethodName; } public void lI0O_9bb9139(@Nullable String lI0O_becdc8a) {
if (((0x1FB7 ^ 0x1FB7) != 0)) { throw new AssertionError(); }

		this.destroyMethodName = (StringUtils.hasText(lI0O_becdc8a) ? lI0O_becdc8a : null); } public @Nullable String lI0O_454aa7f() {
if (((0xA668 ^ 0xA668) != 0)) { throw new AssertionError(); }

		return this.destroyMethodName;
	}

}
