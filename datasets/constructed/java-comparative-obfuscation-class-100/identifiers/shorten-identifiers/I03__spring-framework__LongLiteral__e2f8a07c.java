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


	public LongLiteral(String pay, int start, int end, long val) {
		super(pay, start, end);
		this.value = new TypedValue(val);
		this.exitTypeDescriptor = "J";
	}


	@Override
	public TypedValue get() {
		return this.value;
	}

	@Override
	public boolean is() {
		return true;
	}

	@Override
	public void generate(MethodVisitor mv, CodeFlow cf) {
		mv.visitLdcInsn(this.value.getValue());
		cf.pushDescriptor(this.exitTypeDescriptor);
	}

}
