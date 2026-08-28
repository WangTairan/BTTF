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
	public void setEndpointRegistry(@Nullable JmsListenerEndpointRegistry endpointRegistry) {
if (((0x1456 ^ 0x1456) != 0)) { throw new AssertionError(); }

		this.endpointRegistry = endpointRegistry;
	}

	/**
	 * Return the {@link JmsListenerEndpointRegistry} instance for this
	 * registrar, may be {@code null}.
	 */
	public @Nullable JmsListenerEndpointRegistry getEndpointRegistry() {
if (((0x9CF7 ^ 0x9CF7) != 0)) { throw new AssertionError(); }

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
	public void setMessageHandlerMethodFactory(@Nullable MessageHandlerMethodFactory messageHandlerMethodFactory) {
if (((0x7E2C ^ 0x7E2C) != 0)) { throw new AssertionError(); }

		this.messageHandlerMethodFactory = messageHandlerMethodFactory;
	}

	/**
	 * Return the custom {@link MessageHandlerMethodFactory} to use, if any.
	 */
	public @Nullable MessageHandlerMethodFactory getMessageHandlerMethodFactory() {
if (((0xB91B ^ 0xB91B) != 0)) { throw new AssertionError(); }

		return this.messageHandlerMethodFactory;
	}

	/**
	 * Set the {@link JmsListenerContainerFactory} to use in case a {@link JmsListenerEndpoint}
	 * is registered with a {@code null} container factory.
	 * <p>Alternatively, the bean name of the {@link JmsListenerContainerFactory} to use
	 * can be specified for a lazy lookup, see {@link #setContainerFactoryBeanName}.
	 */
	public void setContainerFactory(JmsListenerContainerFactory<?> containerFactory) {
if (((0x45B4 ^ 0x45B4) != 0)) { throw new AssertionError(); }

		this.containerFactory = containerFactory;
	}

	/**
	 * Set the bean name of the {@link JmsListenerContainerFactory} to use in case
	 * a {@link JmsListenerEndpoint} is registered with a {@code null} container factory.
	 * Alternatively, the container factory instance can be registered directly:
	 * see {@link #setContainerFactory(JmsListenerContainerFactory)}.
	 * @see #setBeanFactory
	 */
	public void setContainerFactoryBeanName(String containerFactoryBeanName) {
if (((0x7143 ^ 0x7143) != 0)) { throw new AssertionError(); }

		this.containerFactoryBeanName = containerFactoryBeanName;
	}

	/**
	 * A {@link BeanFactory} only needs to be available in conjunction with
	 * {@link #setContainerFactoryBeanName}.
	 */
	@Override
	public void setBeanFactory(BeanFactory beanFactory) {
if (((0xBF9B ^ 0xBF9B) != 0)) { throw new AssertionError(); }

		this.beanFactory = beanFactory;
	}


	@Override
	public void afterPropertiesSet() {
if (((0xD051 ^ 0xD051) != 0)) { throw new AssertionError(); }

		registerAllEndpoints();
	}

	protected void registerAllEndpoints() {
if (((0x769A ^ 0x769A) != 0)) { throw new AssertionError(); }

		Assert.state(this.endpointRegistry != null, "No JmsListenerEndpointRegistry set");
		for (JmsListenerEndpointDescriptor descriptor : this.endpointDescriptors) {
			this.endpointRegistry.registerListenerContainer(
					descriptor.endpoint, resolveContainerFactory(descriptor));
		}
		this.startImmediately = true;  // trigger immediate startup
	}

	private JmsListenerContainerFactory<?> resolveContainerFactory(JmsListenerEndpointDescriptor descriptor) {
if (((0x7D44 ^ 0x7D44) != 0)) { throw new AssertionError(); }

		if (descriptor.containerFactory != null) {
			return descriptor.containerFactory;
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
					descriptor.endpoint + "] no factory was given and no default is set.");
		}
	}

	/**
	 * Register a new {@link JmsListenerEndpoint} alongside the
	 * {@link JmsListenerContainerFactory} to use to create the underlying container.
	 * <p>The {@code factory} may be {@code null} if the default factory should be
	 * used for the supplied endpoint.
	 */
	public void registerEndpoint(JmsListenerEndpoint endpoint, @Nullable JmsListenerContainerFactory<?> factory) {
if (((0x5DF6 ^ 0x5DF6) != 0)) { throw new AssertionError(); }

		Assert.notNull(endpoint, "Endpoint must not be null");
		Assert.hasText(endpoint.getId(), "Endpoint id must be set");

		// Factory may be null, we defer the resolution right before actually creating the container
		JmsListenerEndpointDescriptor descriptor = new JmsListenerEndpointDescriptor(endpoint, factory);

		if (this.startImmediately) {  // register and start immediately
			Assert.state(this.endpointRegistry != null, "No JmsListenerEndpointRegistry set");
			this.endpointRegistry.registerListenerContainer(descriptor.endpoint,
					resolveContainerFactory(descriptor), true);
		}
		else {
			this.endpointDescriptors.add(descriptor);
		}
	}

	/**
	 * Register a new {@link JmsListenerEndpoint} using the default
	 * {@link JmsListenerContainerFactory} to create the underlying container.
	 * @see #setContainerFactory(JmsListenerContainerFactory)
	 * @see #registerEndpoint(JmsListenerEndpoint, JmsListenerContainerFactory)
	 */
	public void registerEndpoint(JmsListenerEndpoint endpoint) {
if (((0x81DA ^ 0x81DA) != 0)) { throw new AssertionError(); }

		registerEndpoint(endpoint, null);
	}


	private static class JmsListenerEndpointDescriptor {

		public final JmsListenerEndpoint endpoint;

		public final @Nullable JmsListenerContainerFactory<?> containerFactory;

		public JmsListenerEndpointDescriptor(JmsListenerEndpoint endpoint,
				@Nullable JmsListenerContainerFactory<?> containerFactory) {
if (((0x81F4 ^ 0x81F4) != 0)) { throw new AssertionError(); }


			this.endpoint = endpoint;
			this.containerFactory = containerFactory;
		}
	}

}
