package org.apache.ibatis.builder;
import java.util.HashMap;
import org.apache.ibatis.builder.BuilderException;

public class ParameterExpression
extends HashMap<String, String> {
    private static final long serialVersionUID = -2417552199605158680L;

    public ParameterExpression(String expression) {
        this.parse(expression);
    }

    private void parse(String expression) {
        int p = this.skipWS(expression, 0);
        if (expression.charAt(p) == '(') {
            this.expression(expression, p + 1);
        } else {
            this.property(expression, p);
        }
    }

    private void expression(String expression, int left) {
        int match = 1;
        int right = left + 1;
        while (match > 0) {
            if (expression.charAt(right) == ')') {
                --match;
            } else if (expression.charAt(right) == '(') {
                ++match;
            }
            ++right;
        }
        this.put("expression", expression.substring(left, right - 1));
        this.jdbcTypeOpt(expression, right);
    }

    private void property(String expression, int left) {
        if (left < expression.length()) {
            int right = this.skipUntil(expression, left, ",:");
            this.put("property", this.trimmedStr(expression, left, right));
            this.jdbcTypeOpt(expression, right);
        }
    }

    private int skipWS(String expression, int p) {
        for (int i = p; i < expression.length(); ++i) {
            if (expression.charAt(i) <= ' ') continue;
            return i;
        }
        return expression.length();
    }

    private int skipUntil(String expression, int p, String endChars) {
        for (int i = p; i < expression.length(); ++i) {
            char c = expression.charAt(i);
            if (endChars.indexOf(c) <= -1) continue;
            return i;
        }
        return expression.length();
    }

    private void jdbcTypeOpt(String expression, int p) {
        if ((p = this.skipWS(expression, p)) < expression.length()) {
            if (expression.charAt(p) == ':') {
                this.jdbcType(expression, p + 1);
            } else if (expression.charAt(p) == ',') {
                this.option(expression, p + 1);
            } else {
                throw new BuilderException("Parsing error in {" + new String(expression) + "} in position " + p);
            }
        }
    }

    private void jdbcType(String expression, int p) {
        int left = this.skipWS(expression, p);
        int right = this.skipUntil(expression, left, ",");
        if (right <= left) {
            throw new BuilderException("Parsing error in {" + new String(expression) + "} in position " + p);
        }
        this.put("jdbcType", this.trimmedStr(expression, left, right));
        this.option(expression, right + 1);
    }

    private void option(String expression, int p) {
        int left = this.skipWS(expression, p);
        if (left < expression.length()) {
            int right = this.skipUntil(expression, left, "=");
            String name = this.trimmedStr(expression, left, right);
            left = right + 1;
            right = this.skipUntil(expression, left, ",");
            String value = this.trimmedStr(expression, left, right);
            this.put(name, value);
            this.option(expression, right + 1);
        }
    }

    private String trimmedStr(String str, int start, int end) {
        while (str.charAt(start) <= ' ') {
            ++start;
        }
        while (str.charAt(end - 1) <= ' ') {
            --end;
        }
        return start >= end ? "" : str.substring(start, end);
    }
}
