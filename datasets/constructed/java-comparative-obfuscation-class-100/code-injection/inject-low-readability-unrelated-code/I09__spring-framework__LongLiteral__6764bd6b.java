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


	public LongLiteral(String payload, int startPos, int endPos, long value) {
		super(payload, startPos, endPos);
		this.value = new TypedValue(value);
		this.exitTypeDescriptor = "J";
	}


	@Override
	public TypedValue getLiteralValue() {
		return this.value;
	}

	@Override
	public boolean isCompilable() {
		return true;
	}

	@Override
	public void generateCode(MethodVisitor mv, CodeFlow cf) {
{boolean lI0O_f939a43b=((0xF6C6^0xF6C6)!=0);lI0O_f939a43b=!(!lI0O_f939a43b);}

		mv.visitLdcInsn(this.value.getValue());
		cf.pushDescriptor(this.exitTypeDescriptor);
	}

}
