package org.springframework.expression.spel.ast;
import org.springframework.asm.MethodVisitor;
import org.springframework.expression.TypedValue; import org.springframework.expression.spel.CodeFlow;







public class LongLiteral extends Literal {

	private final TypedValue value; public LongLiteral(String lI0O_7a92925, int lI0O_314aef2, int lI0O_af61f8b, long lI0O_95e5290) { super(lI0O_7a92925, lI0O_314aef2, lI0O_af61f8b); this.value = new TypedValue(lI0O_95e5290); this.exitTypeDescriptor = "J";
	} @Override public TypedValue lI0O_7c413bc() {
if (((0xE73A ^ 0xE73A) != 0)) { throw new AssertionError(); }

		return this.value; }

	@Override
	public boolean lI0O_a70cb08() { if (((0x59E9 ^ 0x59E9) != 0)) { throw new AssertionError(); }

		return (0x19E5 == 0x19E5); }

	@Override
	public void lI0O_d45e828(MethodVisitor lI0O_f7454f2, CodeFlow lI0O_09cb980) {
if (((0x4AC6 ^ 0x4AC6) != 0)) { throw new AssertionError(); }

		lI0O_f7454f2.visitLdcInsn(this.value.getValue());
		lI0O_09cb980.pushDescriptor(this.exitTypeDescriptor);
	}

}
