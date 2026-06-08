package coganscore;

import coganscore.util.IdentifierHeuristics;
import coganscore.util.UnusedImportAnalyzer;

import com.sun.source.tree.AnnotatedTypeTree;
import com.sun.source.tree.ArrayTypeTree;
import com.sun.source.tree.AssignmentTree;
import com.sun.source.tree.BinaryTree;
import com.sun.source.tree.ClassTree;
import com.sun.source.tree.CompilationUnitTree;
import com.sun.source.tree.CompoundAssignmentTree;
import com.sun.source.tree.DoWhileLoopTree;
import com.sun.source.tree.EnhancedForLoopTree;
import com.sun.source.tree.ExpressionStatementTree;
import com.sun.source.tree.ExpressionTree;
import com.sun.source.tree.ForLoopTree;
import com.sun.source.tree.IdentifierTree;
import com.sun.source.tree.IfTree;
import com.sun.source.tree.ImportTree;
import com.sun.source.tree.InstanceOfTree;
import com.sun.source.tree.IntersectionTypeTree;
import com.sun.source.tree.LiteralTree;
import com.sun.source.tree.MemberSelectTree;
import com.sun.source.tree.MethodInvocationTree;
import com.sun.source.tree.MethodTree;
import com.sun.source.tree.NewClassTree;
import com.sun.source.tree.ParameterizedTypeTree;
import com.sun.source.tree.ParenthesizedTree;
import com.sun.source.tree.StatementTree;
import com.sun.source.tree.SwitchTree;
import com.sun.source.tree.Tree;
import com.sun.source.tree.TypeCastTree;
import com.sun.source.tree.TypeParameterTree;
import com.sun.source.tree.UnaryTree;
import com.sun.source.tree.UnionTypeTree;
import com.sun.source.tree.VariableTree;
import com.sun.source.tree.WhileLoopTree;
import com.sun.source.util.TreePath;
import com.sun.source.util.TreeScanner;
import com.sun.source.util.Trees;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.Set;
import java.util.regex.Pattern;
import java.util.regex.PatternSyntaxException;

public class AstLexemeExtractor extends TreeScanner<Void, Void> {
    private final Trees trees;
    private CompilationUnitTree cu;
    private final List<Tree> nodeBuffer = new ArrayList<>();
    private final List<LexemeChunk> chunks = new ArrayList<>();
    private boolean skipForInitVar = false;

    public AstLexemeExtractor(Trees trees) {
        this.trees = trees;
    }

    public List<LexemeChunk> extract(CompilationUnitTree compilationUnit) {
        this.cu = compilationUnit;
        nodeBuffer.clear();
        chunks.clear();

        scan(cu, null);
        for (Tree node : nodeBuffer) {
            chunks.addAll(newChunks(node));
        }

        chunks.sort(Comparator.comparingInt(LexemeChunk::line));
        return new ArrayList<>(chunks);
    }

    // Imports
    @Override
    public Void visitImport(ImportTree node, Void unused) {
        if (node == null || node.getQualifiedIdentifier() == null) {
            return null;
        }

        String imported = node.getQualifiedIdentifier().toString();
        String category = imported.startsWith("java.") || imported.startsWith("javax.")
                ? "stdlib"
                : "external";

        String[] parts = imported.split("\\.");
        String base = parts.length >= 2
                ? parts[parts.length - 2] + "_" + parts[parts.length - 1]
                : parts[0];

        boolean used = true;
        try {
            Set<String> unusedImports = UnusedImportAnalyzer.findUnusedImports(cu.toString());
            used = !unusedImports.contains(imported);
        } catch (Exception ignored) {
            used = true;
        }

        String prefix = used ? "import" : "unused_import";
        LexemeType type = used ? LexemeType.IMPORT : LexemeType.UNUSED_IMPORT;
        addChunk(node, prefix + "_" + category + "_" + base, type);
        return null;
    }

    // Variables
    @Override
    public Void visitIdentifier(IdentifierTree node, Void unused) {
        if (isTypeIdentifier(node)) {
            return super.visitIdentifier(node, unused);
        }
        addNode(node);
        return super.visitIdentifier(node, unused);
    }

    @Override
    public Void visitVariable(VariableTree node, Void unused) {
        if (skipForInitVar) {
            scan(node.getModifiers(), unused);
            scan(node.getInitializer(), unused);
            return null;
        }

        addNode(node);
        scan(node.getModifiers(), unused);
        scan(node.getInitializer(), unused);
        return null;
    }

    @Override
    public Void visitMethod(MethodTree node, Void unused) {
        addNode(node);
        return super.visitMethod(node, unused);
    }

    // Constants
    @Override
    public Void visitLiteral(LiteralTree node, Void unused) {
        addNode(node);
        return super.visitLiteral(node, unused);
    }

    // Structure
    @Override
    public Void visitIf(IfTree node, Void unused) {
        addNode(node);
        scan(node.getCondition(), unused);
        scan(node.getThenStatement(), unused);

        StatementTree elseStatement = node.getElseStatement();
        while (elseStatement instanceof IfTree nested) {
            scan(nested.getCondition(), unused);
            scan(nested.getThenStatement(), unused);
            elseStatement = nested.getElseStatement();
        }
        if (elseStatement != null) {
            scan(elseStatement, unused);
        }
        return null;
    }

    @Override
    public Void visitWhileLoop(WhileLoopTree node, Void unused) {
        addNode(node);
        return super.visitWhileLoop(node, unused);
    }

    @Override
    public Void visitForLoop(ForLoopTree node, Void unused) {
        addNode(node);

        skipForInitVar = true;
        for (StatementTree statement : node.getInitializer()) {
            scan(statement, unused);
        }
        skipForInitVar = false;

        scan(node.getCondition(), unused);
        for (ExpressionStatementTree update : node.getUpdate()) {
            scan(update, unused);
        }
        scan(node.getStatement(), unused);
        return null;
    }

    @Override
    public Void visitEnhancedForLoop(EnhancedForLoopTree node, Void unused) {
        addNode(node);
        return super.visitEnhancedForLoop(node, unused);
    }

    @Override
    public Void visitDoWhileLoop(DoWhileLoopTree node, Void unused) {
        addNode(node);
        return super.visitDoWhileLoop(node, unused);
    }

    @Override
    public Void visitSwitch(SwitchTree node, Void unused) {
        addNode(node);
        return super.visitSwitch(node, unused);
    }

    // Expressions
    @Override
    public Void visitUnary(UnaryTree node, Void unused) {
        addNode(node);
        return super.visitUnary(node, unused);
    }

    @Override
    public Void visitBinary(BinaryTree node, Void unused) {
        addNode(node);
        return super.visitBinary(node, unused);
    }

    @Override
    public Void visitAssignment(AssignmentTree node, Void unused) {
        addNode(node);
        return super.visitAssignment(node, unused);
    }

    @Override
    public Void visitMethodInvocation(MethodInvocationTree node, Void unused) {
        addNode(node);
        return super.visitMethodInvocation(node, unused);
    }

    private void addNode(Tree node) {
        if (node != null) {
            nodeBuffer.add(node);
        }
    }

    private List<LexemeChunk> newChunks(Tree node) {
        List<LexemeChunk> out = new ArrayList<>();
        if (node == null) {
            return out;
        }

        if (addVariableLexemes(out, node)) {
            return out;
        }
        if (addLiteralLexemes(out, node)) {
            return out;
        }
        if (addStructureLexemes(out, node)) {
            return out;
        }
        if (addExpressionLexemes(out, node)) {
            return out;
        }
        return out;
    }

    // Variable lexemes
    private boolean addVariableLexemes(List<LexemeChunk> out, Tree node) {
        if (node instanceof IdentifierTree identifier) {
            String lexeme = normalize(identifier.getName().toString());
            LexemeType type = IdentifierHeuristics.isLikelyJunk(lexeme) ? LexemeType.JUNK : LexemeType.NORMAL;
            addChunk(out, node, lexeme, type);
            return true;
        }

        if (node instanceof VariableTree variable) {
            String name = normalize(variable.getName().toString());
            LexemeType type = IdentifierHeuristics.isLikelyJunk(name) ? LexemeType.JUNK : LexemeType.NORMAL;
            addChunk(out, node, name, type);

            Tree typeTree = variable.getType();
            if (typeTree != null && !name.isEmpty()) {
                addChunk(out, node, joinParts(Arrays.asList(normalize(typeTree.toString()), name)));
            }

            ExpressionTree initializer = variable.getInitializer();
            if (initializer != null && !name.isEmpty()) {
                addChunk(out, node, "def_" + name);
                addChunk(out, node, "def_" + name + "_" + normalize(initializer.toString()));
            }
            return true;
        }

        if (node instanceof MethodTree method) {
            List<String> parts = new ArrayList<>();
            parts.add("def");
            String name = method.getName() == null ? "" : normalize(method.getName().toString());
            if (!name.isEmpty()) {
                parts.add(name);
            }
            for (VariableTree parameter : method.getParameters()) {
                String parameterName = normalize(parameter.getName().toString());
                if (!parameterName.isEmpty()) {
                    parts.add(parameterName);
                }
            }
            addChunk(out, node, joinParts(parts));
            addChunk(out, node, name);
            return true;
        }

        return false;
    }

    // Constant lexemes
    private boolean addLiteralLexemes(List<LexemeChunk> out, Tree node) {
        if (!(node instanceof LiteralTree literal)) {
            return false;
        }

        Object value = literal.getValue();
        if (value instanceof String stringValue) {
            if (isCompilableRegex(stringValue)) {
                for (String token : tokenizeRegex(stringValue)) {
                    addChunk(out, node, joinParts(Arrays.asList("regex", token)), LexemeType.REGEX);
                }
            } else {
                addChunk(out, node, "literal_" + normalize(stringValue));
            }
            return true;
        }

        if (value != null) {
            addChunk(out, node, "literal_" + normalize(String.valueOf(value)));
        }
        return true;
    }

    // Structure lexemes
    private boolean addStructureLexemes(List<LexemeChunk> out, Tree node) {
        if (node instanceof IfTree ifTree) {
            addIfLexemes(out, ifTree);
            return true;
        }

        if (node instanceof WhileLoopTree whileLoop) {
            addChunk(out, node, joinParts(Arrays.asList("while", condString(whileLoop.getCondition()))));
            return true;
        }

        if (node instanceof ForLoopTree forLoop) {
            addForLexeme(out, forLoop);
            return true;
        }

        if (node instanceof EnhancedForLoopTree enhancedForLoop) {
            addChunk(out, node, joinParts(Arrays.asList(
                    "for",
                    normalize(enhancedForLoop.getVariable().getName().toString()),
                    normalize(enhancedForLoop.getExpression().toString())
            )));
            return true;
        }

        if (node instanceof DoWhileLoopTree doWhileLoop) {
            addChunk(out, node, joinParts(Arrays.asList("do-while", condString(doWhileLoop.getCondition()))));
            return true;
        }

        if (node instanceof SwitchTree switchTree) {
            addChunk(out, node, joinParts(Arrays.asList("switch", condString(switchTree.getExpression()))));
            return true;
        }

        return false;
    }

    private void addIfLexemes(List<LexemeChunk> out, IfTree ifTree) {
        List<String> seenConditions = new ArrayList<>();
        String headCondition = condString(ifTree.getCondition());
        seenConditions.add(headCondition);
        addChunk(out, ifTree, joinParts(Arrays.asList("if", headCondition)));

        StatementTree elseStatement = ifTree.getElseStatement();
        while (elseStatement instanceof IfTree nested) {
            String condition = condString(nested.getCondition());
            seenConditions.add(condition);
            addChunk(out, nested, joinParts(Arrays.asList("elif", condition)));
            elseStatement = nested.getElseStatement();
        }

        if (elseStatement != null) {
            List<String> parts = new ArrayList<>();
            parts.add("else");
            for (String condition : seenConditions) {
                if (!condition.isEmpty()) {
                    parts.add("not_" + condition);
                }
            }
            addChunk(out, elseStatement, joinParts(parts));
        }
    }

    private void addForLexeme(List<LexemeChunk> out, ForLoopTree forLoop) {
        List<? extends StatementTree> initializers = forLoop.getInitializer();
        ExpressionTree condition = forLoop.getCondition();
        List<? extends ExpressionStatementTree> updates = forLoop.getUpdate();

        String indexName = guessIndexVarName(initializers, updates, condition);
        String iterTarget = extractIterTargetFromCondition(condition, indexName);
        String startPart = extractNonTrivialStart(initializers);
        String stepPart = extractNonTrivialStep(updates);

        List<String> parts = new ArrayList<>();
        parts.add("for");
        if (!iterTarget.isEmpty()) {
            parts.add(iterTarget);
        }
        if (!startPart.isEmpty()) {
            parts.add(startPart);
        }
        if (!stepPart.isEmpty()) {
            parts.add(stepPart);
        }
        addChunk(out, forLoop, joinParts(parts));
    }

    // Expression lexemes
    private boolean addExpressionLexemes(List<LexemeChunk> out, Tree node) {
        if (node instanceof UnaryTree unaryTree) {
            String lexeme = normalize(unaryTree.toString());
            LexemeType type = unaryTree.getKind() == Tree.Kind.BITWISE_COMPLEMENT
                    ? LexemeType.BITWISE
                    : LexemeType.NORMAL;
            addChunk(out, unaryTree, lexeme, type);
            return true;
        }

        if (node instanceof CompoundAssignmentTree assignment) {
            String lexeme = normalize(assignment.getVariable() + compoundAssignOp(assignment.getKind())
                    + assignment.getExpression());
            LexemeType type = isBitwiseAssignKind(assignment.getKind()) ? LexemeType.BITWISE : LexemeType.NORMAL;
            addChunk(out, assignment, lexeme, type);
            return true;
        }

        if (node instanceof BinaryTree binaryTree) {
            LexemeType type = isBitwiseKind(binaryTree.getKind()) ? LexemeType.BITWISE : LexemeType.NORMAL;
            addChunk(out, binaryTree, normalize(binaryTree.toString()), type);

            Tree.Kind op = binaryTree.getKind();
            ExpressionTree current = binaryTree.getLeftOperand();
            while (current instanceof BinaryTree leftBinary && leftBinary.getKind() == op) {
                LexemeType leftType = isBitwiseKind(leftBinary.getKind()) ? LexemeType.BITWISE : LexemeType.NORMAL;
                addChunk(out, leftBinary, normalize(leftBinary.toString()), leftType);
                current = leftBinary.getLeftOperand();
            }
            return true;
        }

        if (node instanceof MethodInvocationTree call) {
            List<String> parts = new ArrayList<>();
            parts.add(String.valueOf(call.getMethodSelect()));
            for (ExpressionTree argument : call.getArguments()) {
                parts.add(String.valueOf(argument));
            }
            addChunk(out, node, joinParts(parts));
            return true;
        }

        return false;
    }

    // Shared builders
    private void addChunk(Tree anchor, String lexeme, LexemeType type) {
        addChunk(chunks, anchor, lexeme, type);
    }

    private void addChunk(List<LexemeChunk> out, Tree anchor, String lexeme) {
        addChunk(out, anchor, lexeme, LexemeType.NORMAL);
    }

    private void addChunk(List<LexemeChunk> out, Tree anchor, String lexeme, LexemeType type) {
        String normalized = normalize(lexeme);
        if (normalized.isEmpty()) {
            return;
        }

        long start = trees.getSourcePositions().getStartPosition(cu, anchor);
        int line = (int) cu.getLineMap().getLineNumber(start);
        out.add(new LexemeChunk(normalized, line, type));
    }

    private String condString(ExpressionTree expression) {
        if (expression == null) {
            return "";
        }
        return normalize(unwrapParens(expression).toString());
    }

    private ExpressionTree unwrapParens(ExpressionTree expression) {
        while (expression instanceof ParenthesizedTree parenthesized) {
            expression = parenthesized.getExpression();
        }
        return expression;
    }

    private String joinParts(List<String> parts) {
        StringBuilder builder = new StringBuilder();
        boolean first = true;
        for (String part : parts) {
            String normalized = normalize(part);
            if (normalized.isEmpty()) {
                continue;
            }
            if (!first) {
                builder.append('_');
            }
            builder.append(normalized);
            first = false;
        }
        return builder.toString();
    }

    private String normalize(String value) {
        if (value == null) {
            return "";
        }
        return value.trim().replaceAll("\\s+", "");
    }

    // Type filters
    private boolean isTypeIdentifier(IdentifierTree identifier) {
        TreePath path = TreePath.getPath(cu, identifier);
        if (path == null) {
            return false;
        }

        TreePath current = path;
        while (current.getParentPath() != null) {
            Tree child = current.getLeaf();
            Tree parent = current.getParentPath().getLeaf();

            if (parent instanceof ParameterizedTypeTree
                    || parent instanceof AnnotatedTypeTree
                    || parent instanceof ArrayTypeTree
                    || parent instanceof MemberSelectTree
                    || parent instanceof UnionTypeTree
                    || parent instanceof IntersectionTypeTree) {
                current = current.getParentPath();
                continue;
            }

            if (parent instanceof VariableTree variable && child == variable.getType()) {
                return true;
            }
            if (parent instanceof MethodTree method && child == method.getReturnType()) {
                return true;
            }
            if (parent instanceof NewClassTree newClass && child == newClass.getIdentifier()) {
                return true;
            }
            if (parent instanceof TypeCastTree typeCast && child == typeCast.getType()) {
                return true;
            }
            if (parent instanceof InstanceOfTree instanceOf && child == instanceOf.getType()) {
                return true;
            }
            if (parent instanceof ClassTree classTree) {
                if (child == classTree.getExtendsClause()) {
                    return true;
                }
                for (Tree impl : classTree.getImplementsClause()) {
                    if (child == impl) {
                        return true;
                    }
                }
            }
            if (parent instanceof TypeParameterTree typeParameter) {
                if (child == typeParameter.getName()) {
                    return true;
                }
                for (Tree bound : typeParameter.getBounds()) {
                    if (child == bound) {
                        return true;
                    }
                }
            }
            break;
        }

        TreePath qualifierPath = path;
        while (qualifierPath.getParentPath() != null
                && qualifierPath.getParentPath().getLeaf() instanceof MemberSelectTree memberSelect) {
            if (memberSelect.getExpression() == qualifierPath.getLeaf()) {
                qualifierPath = qualifierPath.getParentPath();
            } else {
                break;
            }
        }
        return qualifierPath != path;
    }

    // Operator helpers
    private boolean isBitwiseKind(Tree.Kind kind) {
        return switch (kind) {
            case AND, OR, XOR, LEFT_SHIFT, RIGHT_SHIFT, UNSIGNED_RIGHT_SHIFT -> true;
            default -> false;
        };
    }

    private boolean isBitwiseAssignKind(Tree.Kind kind) {
        return switch (kind) {
            case AND_ASSIGNMENT, OR_ASSIGNMENT, XOR_ASSIGNMENT,
                 LEFT_SHIFT_ASSIGNMENT, RIGHT_SHIFT_ASSIGNMENT, UNSIGNED_RIGHT_SHIFT_ASSIGNMENT -> true;
            default -> false;
        };
    }

    private String compoundAssignOp(Tree.Kind kind) {
        return switch (kind) {
            case PLUS_ASSIGNMENT -> "+=";
            case MINUS_ASSIGNMENT -> "-=";
            case MULTIPLY_ASSIGNMENT -> "*=";
            case DIVIDE_ASSIGNMENT -> "/=";
            case REMAINDER_ASSIGNMENT -> "%=";
            case AND_ASSIGNMENT -> "&=";
            case OR_ASSIGNMENT -> "|=";
            case XOR_ASSIGNMENT -> "^=";
            case LEFT_SHIFT_ASSIGNMENT -> "<<=";
            case RIGHT_SHIFT_ASSIGNMENT -> ">>=";
            case UNSIGNED_RIGHT_SHIFT_ASSIGNMENT -> ">>>=";
            default -> "=";
        };
    }

    // Regex constants
    private boolean isCompilableRegex(String value) {
        if (value == null || value.length() < 2) {
            return false;
        }
        try {
            Pattern.compile(value);
            return true;
        } catch (PatternSyntaxException ex) {
            return false;
        }
    }

    private List<String> tokenizeRegex(String value) {
        List<String> out = new ArrayList<>();
        int n = value.length();
        StringBuilder buffer = new StringBuilder();
        Runnable flush = () -> {
            if (!buffer.isEmpty()) {
                out.add(buffer.toString());
                buffer.setLength(0);
            }
        };

        for (int i = 0; i < n; ) {
            char c = value.charAt(i);
            if (c == '[') {
                flush.run();
                int j = i + 1;
                boolean escaped = false;
                while (j < n) {
                    char next = value.charAt(j);
                    if (escaped) {
                        escaped = false;
                        j++;
                        continue;
                    }
                    if (next == '\\') {
                        escaped = true;
                        j++;
                        continue;
                    }
                    if (next == ']') {
                        j++;
                        break;
                    }
                    j++;
                }
                out.add(value.substring(i, Math.min(j, n)));
                i = j;
                continue;
            }

            if (c == '(') {
                flush.run();
                int j = i + 1;
                if (j < n && value.charAt(j) == '?') {
                    j++;
                    while (j < n) {
                        char next = value.charAt(j);
                        if (next == ':' || next == ')') {
                            j++;
                            break;
                        }
                        j++;
                    }
                    out.add(value.substring(i, Math.min(j, n)));
                    i = j;
                } else {
                    out.add("(");
                    i++;
                }
                continue;
            }

            if (c == ')') {
                flush.run();
                out.add(")");
                i++;
                continue;
            }

            if (c == '*' || c == '+' || c == '?') {
                flush.run();
                int j = i + 1;
                if (j < n && value.charAt(j) == '?') {
                    j++;
                }
                out.add(value.substring(i, j));
                i = j;
                continue;
            }

            if (c == '{') {
                flush.run();
                int j = i + 1;
                while (j < n && value.charAt(j) != '}') {
                    j++;
                }
                if (j < n) {
                    j++;
                }
                if (j < n && value.charAt(j) == '?') {
                    j++;
                }
                out.add(value.substring(i, Math.min(j, n)));
                i = j;
                continue;
            }

            if (c == '|' || c == '^' || c == '$') {
                flush.run();
                out.add(String.valueOf(c));
                i++;
                continue;
            }

            if (c == '\\') {
                flush.run();
                if (i + 1 < n) {
                    out.add(value.substring(i, i + 2));
                    i += 2;
                } else {
                    out.add("\\");
                    i++;
                }
                continue;
            }

            buffer.append(c);
            i++;
        }
        flush.run();
        return out;
    }

    // For loops
    private String extractNonTrivialStart(List<? extends StatementTree> initializers) {
        if (initializers == null) {
            return "";
        }
        for (StatementTree statement : initializers) {
            if (statement instanceof VariableTree variable) {
                String name = normalize(variable.getName().toString());
                ExpressionTree initializer = variable.getInitializer();
                String rhs = initializer == null ? "" : normalize(initializer.toString());
                if (!name.isEmpty() && !rhs.isEmpty() && !isZeroOrOne(rhs)) {
                    return name + "=" + rhs;
                }
            }
        }
        return "";
    }

    private boolean isZeroOrOne(String value) {
        String normalized = value.replaceAll("[()\\s]", "");
        return normalized.equals("0") || normalized.equals("1")
                || normalized.equals("0L") || normalized.equals("1L")
                || normalized.equals("0.0") || normalized.equals("1.0");
    }

    private String extractNonTrivialStep(List<? extends ExpressionStatementTree> updates) {
        if (updates == null) {
            return "";
        }
        for (ExpressionStatementTree update : updates) {
            String expression = normalize(String.valueOf(update.getExpression()));
            if (!expression.isEmpty() && !isSimpleIncDec(expression)) {
                return expression;
            }
        }
        return "";
    }

    private boolean isSimpleIncDec(String expression) {
        return expression.endsWith("++") || expression.startsWith("++")
                || expression.endsWith("--") || expression.startsWith("--");
    }

    private String guessIndexVarName(List<? extends StatementTree> initializers,
                                     List<? extends ExpressionStatementTree> updates,
                                     ExpressionTree condition) {
        if (initializers != null) {
            for (StatementTree statement : initializers) {
                if (statement instanceof VariableTree variable) {
                    String name = normalize(variable.getName().toString());
                    if (!name.isEmpty()) {
                        return name;
                    }
                }
            }
        }
        if (updates != null) {
            for (ExpressionStatementTree update : updates) {
                String expression = normalize(String.valueOf(update.getExpression()));
                if (expression.endsWith("++") || expression.endsWith("--")) {
                    return normalize(expression.substring(0, expression.length() - 2));
                }
                if (expression.startsWith("++") || expression.startsWith("--")) {
                    return normalize(expression.substring(2));
                }
                int position = expression.indexOf("+=");
                if (position > 0) {
                    return normalize(expression.substring(0, position));
                }
                position = expression.indexOf("-=");
                if (position > 0) {
                    return normalize(expression.substring(0, position));
                }
                position = expression.indexOf("=");
                if (position > 0) {
                    return normalize(expression.substring(0, position));
                }
            }
        }
        if (condition instanceof BinaryTree binaryTree) {
            String left = normalize(binaryTree.getLeftOperand().toString());
            if (!left.isEmpty()) {
                return left;
            }
        }
        return "";
    }

    private String extractIterTargetFromCondition(ExpressionTree condition, String indexName) {
        if (!(condition instanceof BinaryTree binaryTree)) {
            return "";
        }

        String left = normalize(binaryTree.getLeftOperand().toString());
        String right = normalize(binaryTree.getRightOperand().toString());
        if (!indexName.isEmpty()) {
            if (left.equals(indexName)) {
                return right;
            }
            if (right.equals(indexName)) {
                return left;
            }
        }

        boolean rightLooksLikeTarget = right.contains(".") || right.endsWith(")");
        boolean leftLooksLikeTarget = left.contains(".") || left.endsWith(")");
        if (rightLooksLikeTarget && !leftLooksLikeTarget) {
            return right;
        }
        if (leftLooksLikeTarget && !rightLooksLikeTarget) {
            return left;
        }
        return right;
    }
}
