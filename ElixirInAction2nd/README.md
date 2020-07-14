My main takeaways.

# Ch1 to Ch5

Mostly learning Elixir while working through Exercism; any comment on [my solutions](https://exercism.io/profiles/b1az) is appreciated.

# Ch6

Learning about the `GenServer`.

* From [a bare TodoServer as in Ch6](https://github.com/b1az/Kata-Elixir/commit/a3f6162aabbaabad69993850e380be0faf48a191)
* to a [shortened TodoServer, with generic code moved into a limited, hand-rolled 'GenServer'](https://github.com/b1az/Kata-Elixir/commit/0213aa9f6dd1a3b8f3cffb23eff58918856ebd5e)
* and finally, [using the `GenServer` itself](https://github.com/b1az/Kata-Elixir/commit/350641bd5fe7a12cd633af2b2a94bc11c250d284).

# Ch7

## 7.2
Scale to multiple todo-lists by vending out a `Todo.Server` per todo-list via `Todo.Cache`. (Testing intermezzo in section 7.2.2.) `Todo.Cache` might now itself be a bottleneck, but an empirical test on localhost gives 100+k reqs/s for its only functionality, `server_process`. The system as a whole is now scalable since these 100k reqs will each process their own todo-list in their own memory. And operations on the same todo-list will happen in the same process, sequentially and thus without race conditions.

## 7.3
Add persistance via `Todo.Database`, as a singleton process using `__MODULE__` in `GenServer.start/3`. Since this function returns only after the process has been `init`ed, and fetching from DB might take a while, we resort to `send`ing the process an internal message, thus delaying the `:real_init` to the `handle_info` callback.

> With OTP 21, would we now rather use [`handle_continue`](https://elixirschool.com/blog/til-genserver-handle-continue/)?

Sections 7.3.3 & 7.3.4 point out & address the singleton DB process as a potential bottleneck:

- bypass singleton DB [100k reqs would still overload I/O]
- have DB `spawn` its concurrent (unbounded) workers [same issue]
- have DB `spawn` its concurrent (bounded/pooled) workers [chosen solution for this scenario, obviously dependant on a particular DB implementation]

Use the approach in the last bulletpoint as [an exercise in section 7.3.5](https://github.com/b1az/Kata-Elixir/commit/aa4d9ab32492332043d4d4355194f9a358d7e86f).

# Ch8

Overview of 3 error types. On inter-process error-handling via links (bi-directional) and monitors (uni-). Introduce `Supervisor`. Showcase how a too loose structure leads to dangling processes that continue to consume memory and CPU. OTOH, how a too strict structure might be torn down on a slightest of errors. More fine-grained approach is presented in Ch9.

# Ch9
## 9.1
Supervision tree that limits error fallout to conceptually distinct subtrees; e.g. database and its workers. Wrap `Register` for service discovery and use it via `:via` tuples.

## 9.2
`Supervisor` was used for a predefined # of DB-workers. Now use `DynamicSupervisor` for a dynamic # of todo-servers.


# Ch10
## 10.1
- Awaited `Task`: `Task.await(Task.aync(fn -> ... end))`; `aync/1` links to the starter process (task is aborted if parent/starter dies, and vice-versa (unless parent is trapping)).
- Non-awaited `Task`: `Task.start_link(fn -> ... end)`. It is (in)directly put under a `Supervisor` and thus "not directly linked to the caller" and can't be awaited on.

## 10.2
`Agent` is a simpler (and limited) version of `GenServer`: if you only use `init/1`, `handle_cast/2`, and `handle_call/3` of the latter, you can replace it with `Agent`.

Not worth using: slight savings in boilerplate reduction are cancelled-out by not even thinking about the choice and just always going straight for `GenServer`. Showcase self-terminating processes via adding a `:timeout` arg to all `GenServer` callbacks.

## 10.3
ETS table as a more performant but limited state-sharing approach, compared to `GenServer`.

## 10.3.4
Exercise implementing `SimpleRegistry` as 1) a `GenServer` and then 2) using an elixirETS table.

# Ch11
## 11.1
Anatomy and runtime of an `Application`. Streamlined testing with the system starting automatically.

## 11.2
Outsource pooling `DatabaseWorker`s to a proven lib, Poolboy. Present Erlang's `:observer` tool.

## 11.3
Add a basic HTTP interface via Cowboy & Plug. Use the latter's `plug`, `post`, `get` macros to add 2 endpoints. For `post`, analyze `call` vs `cast` performance; mention `GenStage` as an intermediate solution/process.

## 11.4
`Mix.Config` and `Mix.env/0`. Default scripts locations `mix` looks for in `config/`.

# Ch12

## 12.1

Using `--sname` (short name) to turn a BEAM instance into a node:
```
iex --sname node1@localhost
```

Inter-node communication via `Node.spawn/2`.

Process discovery using `:global` and `:pg2` modules.

From a node-A do `Node.connect(:node-B@another_host)`. Then `Process.monitor` on some `:global`ly registered process. When that process terminates, node-A gets a `:DOWN` message.

## 12.2
Relying on a `:global` registration is a simple solution for a distributed registration of `Todo.Server`s. It keeps working if a node joins or leaves the cluster, but it's relatively slow as it grabs a cluster-wide lock on each lookup (even if `Server` is already running). This can be slightly improved by an explicit `:global.whereis_name/1` lookup.

An alternative is proposed: explicitly map `todo_list_name` to a node-index. This greatly reduces network communication, but leaves you to handle the complexity of (performantly, via 'consistent hashing') refreshing these indices when a node leaves/joins. See 3rd party modules: [Syn](https://github.com/ostinelli/syn) or [Swarm](https://github.com/bitwalker/swarm).

Using `:rpc.multicall/4` to replicate `Database`.

Using `:net_kernel.monitor_nodes/1` to get notifications on changes in connected nodes.

## 12.3

  - "arbitrary_prefix@host" is a short name (`--sname`)
  - "arbitrary_prefix@host.domain" is a long name (`--name`)

Per machine cookie in `~/.erlang.cookie`, also seen with `Node.get_cookie`.


Unclear paragpraph on p.331:

> "Cookies provide a bare minimum of security and also help prevent a fully connected cluster where all nodes can directly talk to each other. For example, let’s say you want to connect node A to B, and B to C, but you don’t want to connect A and C. This can be done by assigning different cookies to all the nodes and then, in A and C, using the Node.set_cookie/2 function, which allows you to explicitly set different cookies that need to be used when connecting to different nodes."

If you’re behind a firewall, you need to open port 4369 (EPMD) and the range of ports on which your node will listen:

```elixir
iex                                           \
  --erl '-kernel inet_dist_listen_min 10000'    \
  --erl '-kernel inet_dist_listen_max 10200'    \
  --sname node1@localhost
```

# Ch13

`iex --remsh` for remote shell.

Add `:distillery` lib for building OTP releases, minimal `rel/config.exs` and run `mix release`.

Anatomy of `_build/prod/rel/`. `extra_applications: [:runtime_tools]` for enabling `:observer` app.

Debugging with `pry`, `:timer.tc/1`, `loggger`, `benchfella`, ...

Tracing with `:sys.trace`, `:erlang.trace` and `:dbg`:

```elixir
iex(tracer@127.0.0.1)1> :dbg.tracer()
iex(tracer@127.0.0.1)2> :dbg.n(:'todo@127.0.0.1')
iex(tracer@127.0.0.1)3> :dbg.p(:all, [:call])
iex(tracer@127.0.0.1)4> :dbg.tp(Todo.Server, [])
```

`recon` lib.
