package com.google.common.eventbus;
import com.google.errorprone.annotations.Keep;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;















@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
@Keep
public @interface Subscribe {}
