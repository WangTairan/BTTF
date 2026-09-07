package org.springframework.jms.config;
import java.util.ArrayList;
import java.util.List;
import org.jspecify.annotations.Nullable;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.BeanFactoryAware;
import org.springframework.beans.factory.InitializingBean;
import org.springframework.messaging.handler.annotation.support.DefaultMessageHandlerMethodFactory;
import org.springframework.messaging.handler.annotation.support.MessageHandlerMethodFactory;
import org.springframework.util.Assert;

/**
 * Helper bean for registering {@link JmsListenerEndpoint} with a {@link JmsListenerEndpointRegistry}.
 *
 * @author Stephane Nicoll
 * @author Juergen Hoeller
 * @since 4.1
 * @see org.springframework.jms.annotation.JmsListenerConfigurer
 */
public class JmsListenerEndpointRegistrar implements BeanFactoryAware, InitializingBean {

	private @Nullable JmsListenerEndpointRegistry endpointRegistry;

	private @Nullable MessageHandlerMethodFactory messageHandlerMethodFactory;

	private @Nullable JmsListenerContainerFactory<?> containerFactory;

	private @Nullable String containerFactoryBeanName;

	private @Nullable BeanFactory beanFactory;

	private final List<JmsListenerEndpointDescriptor> endpointDescriptors = new ArrayList<>();

	private boolean startImmediately;


	/**
	 * Set the {@link JmsListenerEndpointRegistry} instance to use.
	 */
	public void a(@Nullable JmsListenerEndpointRegistry a) {
		this.endpointRegistry = a;
	}

	/**
	 * Return the {@link JmsListenerEndpointRegistry} instance for this
	 * registrar, may be {@code null}.
	 */
	public @Nullable JmsListenerEndpointRegistry b() {
		return this.endpointRegistry;
	}

	/**
	 * Set the {@link MessageHandlerMethodFactory} to use to configure the message
	 * listener responsible to serve an endpoint detected by this processor.
	 * <p>By default, {@link DefaultMessageHandlerMethodFactory} is used and it
	 * can be configured further to support additional method arguments
	 * or to customize conversion and validation support. See
	 * {@link DefaultMessageHandlerMethodFactory} javadoc for more details.
	 */
	public void c(@Nullable MessageHandlerMethodFactory b) {
		this.messageHandlerMethodFactory = b;
	}

	/**
	 * Return the custom {@link MessageHandlerMethodFactory} to use, if any.
	 */
	public @Nullable MessageHandlerMethodFactory d() {
		return this.messageHandlerMethodFactory;
	}

	/**
	 * Set the {@link JmsListenerContainerFactory} to use in case a {@link JmsListenerEndpoint}
	 * is registered with a {@code null} container factory.
	 * <p>Alternatively, the bean name of the {@link JmsListenerContainerFactory} to use
	 * can be specified for a lazy lookup, see {@link #setContainerFactoryBeanName}.
	 */
	public void e(JmsListenerContainerFactory<?> c) {
		this.containerFactory = c;
	}

	/**
	 * Set the bean name of the {@link JmsListenerContainerFactory} to use in case
	 * a {@link JmsListenerEndpoint} is registered with a {@code null} container factory.
	 * Alternatively, the container factory instance can be registered directly:
	 * see {@link #setContainerFactory(JmsListenerContainerFactory)}.
	 * @see #setBeanFactory
	 */
	public void f(String d) {
		this.containerFactoryBeanName = d;
	}

	/**
	 * A {@link BeanFactory} only needs to be available in conjunction with
	 * {@link #setContainerFactoryBeanName}.
	 */
	@Override
	public void g(BeanFactory e) {
		this.beanFactory = e;
	}


	@Override
	public void h() {
		i();
	}

	protected void i() {
		Assert.state(this.endpointRegistry != null, "No JmsListenerEndpointRegistry set");
		for (JmsListenerEndpointDescriptor f : this.endpointDescriptors) {
			this.endpointRegistry.registerListenerContainer(
					f.endpoint, j(f));
		}
		this.startImmediately = true;  // trigger immediate startup
	}

	private JmsListenerContainerFactory<?> j(JmsListenerEndpointDescriptor g) {
		if (g.containerFactory != null) {
			return g.containerFactory;
		}
		else if (this.containerFactory != null) {
			return this.containerFactory;
		}
		else if (this.containerFactoryBeanName != null) {
			Assert.state(this.beanFactory != null, "BeanFactory must be set to obtain container factory by bean name");
			// Consider changing this if live change of the factory is required...
			this.containerFactory = this.beanFactory.getBean(
					this.containerFactoryBeanName, JmsListenerContainerFactory.class);
			return this.containerFactory;
		}
		else {
			throw new IllegalStateException("Could not resolve the " +
					JmsListenerContainerFactory.class.getSimpleName() + " to use for [" +
					g.endpoint + "] no factory was given and no default is set.");
		}
	}

	/**
	 * Register a new {@link JmsListenerEndpoint} alongside the
	 * {@link JmsListenerContainerFactory} to use to create the underlying container.
	 * <p>The {@code factory} may be {@code null} if the default factory should be
	 * used for the supplied endpoint.
	 */
	public void k(JmsListenerEndpoint h, @Nullable JmsListenerContainerFactory<?> i) {
		Assert.notNull(h, "Endpoint must not be null");
		Assert.hasText(h.getId(), "Endpoint id must be set");

		// Factory may be null, we defer the resolution right before actually creating the container
		JmsListenerEndpointDescriptor j = new JmsListenerEndpointDescriptor(h, i);

		if (this.startImmediately) {  // register and start immediately
			Assert.state(this.endpointRegistry != null, "No JmsListenerEndpointRegistry set");
			this.endpointRegistry.registerListenerContainer(j.endpoint,
					j(j), true);
		}
		else {
			this.endpointDescriptors.add(j);
		}
	}

	/**
	 * Register a new {@link JmsListenerEndpoint} using the default
	 * {@link JmsListenerContainerFactory} to create the underlying container.
	 * @see #setContainerFactory(JmsListenerContainerFactory)
	 * @see #registerEndpoint(JmsListenerEndpoint, JmsListenerContainerFactory)
	 */
	public void k(JmsListenerEndpoint k) {
		k(k, null);
	}


	private static class JmsListenerEndpointDescriptor {

		public final JmsListenerEndpoint endpoint;

		public final @Nullable JmsListenerContainerFactory<?> containerFactory;

		public JmsListenerEndpointDescriptor(JmsListenerEndpoint l,
				@Nullable JmsListenerContainerFactory<?> m) {

			this.endpoint = l;
			this.containerFactory = m;
		}
	}

}
