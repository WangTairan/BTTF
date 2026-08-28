package org.springframework.expression.spel.ast;
import org.springframework.asm.MethodVisitor;
import org.springframework.expression.TypedValue;
import org.springframework.expression.spel.CodeFlow;

/**
 * Expression language AST node that represents a long integer literal.
 *
 * @author Andy Clement
 * @since 3.0
 */
public class LongLiteral extends Literal {

	private final TypedValue value;


	public LongLiteral(String a, int b, int c, long d) {
		super(a, b, c);
		this.value = new TypedValue(d);
		this.exitTypeDescriptor = "J";
	}


	@Override
	public TypedValue a() {
		return this.value;
	}

	@Override
	public boolean b() {
		return true;
	}

	@Override
	public void c(MethodVisitor e, CodeFlow f) {
		e.visitLdcInsn(this.value.getValue());
		f.pushDescriptor(this.exitTypeDescriptor);
	}

}
