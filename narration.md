# Human narrator script

Companion to the silent video. These chapter times come from the animation, not recorded speech.

## 01 · How do we get there?

Start: 0.00s · Visual duration: 22.45s

Imagine you are in Arad and want to reach Bucharest. You can follow the roads, but there is more than one way to go. Before choosing an algorithm, we need to decide what a good route means. Here, every road has a distance in kilometres. We want the route with the smallest total distance. How could we find it without checking every possible journey?

## 02 · Which route is shorter?

Start: 22.45s · Visual duration: 22.87s

Try these two journeys. One passes through Fagaras and uses three roads: 140 plus 99 plus 211, or 450 kilometres. Another passes through Rimnicu Vilcea and Pitesti. It uses four roads, but its total is only 418 kilometres. Counting roads would choose the wrong journey. We need a search that keeps track of the distance already travelled.

## 03 · Follow the cheapest discovery

Start: 45.32s · Visual duration: 31.95s

Start at Arad with a cost of zero. Each time we reach a new city, remember the cheapest cost discovered so far. Extend the route with the smallest cost, then update its neighbours. The purple connections show those discoveries, including replacements when a cheaper route is found. Only after seeing the process do we give it a name: uniform cost search, or UCS. Its priority is the distance already paid, usually written g.

## 04 · Why can we trust that choice?

Start: 77.27s · Visual duration: 19.23s

Why is choosing the cheapest discovered route enough? Suppose the goal is selected, but a cheaper route still exists. Follow that cheaper route from the start until it leaves the settled region. Its first unsettled city must have a discovered cost no greater than that cheaper route's total. Roads have nonnegative costs, so that city would have been selected before the goal. This contradiction explains why UCS waits until the goal is selected, not merely discovered.

## 05 · Why search away from the goal?

Start: 96.50s · Visual duration: 18.73s

UCS is reliable, but look at the branches toward Timisoara and Zerind. Their early costs are small, so UCS explores them even though they do not belong to our final route. It only asks what we have paid so far. It says nothing about the remaining journey. Could we use an estimate of the distance still to go, without losing the guarantee of a shortest route?

## 06 · What if we estimate the rest?

Start: 115.23s · Visual duration: 21.77s

At Rimnicu Vilcea, we have paid 220 kilometres. Suppose our lower-bound estimate for the rest is 198. Together they give a whole-trip estimate of 418. We can rank cities using this total instead of the cost already paid alone. This is the idea behind A star. The familiar equation, f equals g plus h, simply names the three pieces we have just built. But what kind of estimate can we safely use?

## 07 · How optimistic must we be?

Start: 137.00s · Visual duration: 22.87s

An estimate is useful only if we understand its promise. For a remaining journey of 198 kilometres, an estimate of 160 is optimistic. An estimate of 230 is too high and could make us dismiss a route that is actually best. The safe condition is that h never exceeds the true remaining shortest distance d. This property is called admissibility. Our implementation also reopens a city if it later discovers a cheaper route to it. Now we need a way to build an optimistic estimate.

## 08 · Can we solve an easier journey?

Start: 159.87s · Visual duration: 25.03s

One approach is to loosen the rules of the journey. A road has a displacement vector and a cost. A real route must connect roads end to end. Imagine instead buying fractions of road vectors, even if those roads do not form a connected trip, provided their sum reaches the required displacement. We minimize the total cost of that mixture. This easier problem is a linear program, or LP. We use schematic map coordinates, not geographic straight-line distance.

## 09 · Why is this a lower bound?

Start: 184.90s · Visual duration: 21.27s

Keep the same arrows on screen. A real shortest route is one allowed mixture: set its directed-edge coefficients to one and the others to zero. The intermediate positions cancel, leaving the displacement from start to goal. With positive road costs, a shortest route can be simple, so an edge need not be bought more than once. The LP also permits fractional choices, so its minimum cannot exceed the real route cost. Here the stored value is 388.21 kilometres, below 418. The browser uses a precomputed table; its adjacency shortcut and rounding are separately checked on this graph.

## 10 · What can a landmark tell us?

Start: 206.17s · Visual duration: 21.80s

There is another way to estimate the remaining journey. Choose a landmark such as Giurgiu, and measure shortest road distances from it. Arad is 508 kilometres away; Bucharest is 90. Their difference is 418. This particular landmark is unusually strong because Giurgiu connects only through Bucharest. But why should subtracting distances to a landmark give a safe lower bound in general?

## 11 · Why subtract distances?

Start: 227.97s · Visual duration: 26.53s

A shortest road distance from landmark L to city n cannot exceed a trip from L through t to n. Rearrange that statement, then swap n and t. Together the two inequalities say that the absolute difference of landmark distances is at most the distance between n and t. Repeat this for several landmarks and keep the strongest bound. This is the landmark idea behind ALT: A star, landmarks, and the triangle inequality. The argument here uses an undirected road network.

## 12 · Which estimate should we keep?

Start: 254.50s · Visual duration: 18.67s

We now have two answers to the same question: how much journey remains? The LP gives 388.21 kilometres, while our landmark estimate gives 418. Both are safe lower bounds, so their maximum is safe too. Adding them would count the same remaining journey twice and overestimate. These estimates can guide A star, but a search still advances from one starting point. Could we also work backwards from the destination?

## 13 · Why is the maximum still safe?

Start: 273.17s · Visual duration: 21.43s

We now have two admissible bounds, and we keep their maximum. Picture the true remaining distance as a ceiling. Each estimate stays below it. If both stay below the ceiling, so does the taller of the two. That is all safety requires. The same picture gives a second property. The taller estimate is never smaller than either component, so taking the maximum can only sharpen the bound, never weaken it. Here the LP offers two hundred ninety-eight and the landmark bound two hundred fifty-eight against a true distance of three hundred sixty-six. Their maximum is safe, and it is the stronger of the two.

## 14 · Are the bounds safe everywhere?

Start: 294.60s · Visual duration: 22.33s

One example proves nothing on its own. Twenty cities give three hundred and eighty ordered pairs. For each pair we computed the true shortest distance, then placed the estimate against it. Plot the true distance on one axis and the estimate on the other. The diagonal is the ceiling: an estimate may touch it but never cross it. Every LP value lies below. Every landmark value lies below. And their maximum, the estimate we actually use, lies below on all three hundred and eighty pairs. Admissibility here is measured, not assumed.

## 15 · Does the ensemble sharpen the bound?

Start: 316.93s · Visual duration: 20.37s

How close does each bound come? Measure the estimate as a fraction of the true distance, averaged over all pairs. The vector-decomposition LP alone reaches zero point seven three. The landmark bound alone reaches zero point nine eight. Their maximum reaches zero point nine nine, and by construction it is never below either component. On most pairs the landmark bound is already close, so the maximum simply keeps it. On the remaining pairs the LP is the deciding term. The ensemble draws on both methods, and its safety never rests on a single one.

## 16 · Do more landmarks help?

Start: 337.30s · Visual duration: 17.97s

The landmark bound comes from a maximum over landmarks, so adding landmarks can only raise it. With two landmarks the bound reaches zero point nine zero of the true distance. With four it reaches zero point nine seven. With eight it reaches zero point nine eight. Each step is at least as tight as the last, because we take the maximum over a larger set of candidates. None of these steps can break admissibility. More landmarks cost more offline preprocessing, but on this map the gain is real and the safety is unchanged.

## 17 · Which bound wins where?

Start: 355.27s · Visual duration: 17.47s

The ensemble takes the larger of the two bounds, so it is worth seeing which one that is. Fix the goal at Bucharest and compare the two estimates city by city. Across the map the landmark bound is usually the taller, so the maximum simply keeps it. But it is not always. On a few pairs the vector-decomposition LP is the larger, and there the maximum keeps the LP instead. That is the point of taking a maximum over two independent methods: whichever is stronger for this query is the one that guides the search.

## 18 · When is the estimate exact?

Start: 372.73s · Visual duration: 16.65s

Sometimes a landmark gives not just a bound but the exact remainder. Giurgiu connects only through Bucharest. For any city, its distance to Giurgiu minus the ninety kilometres from Giurgiu to Bucharest equals its distance to Bucharest exactly. A degree-one landmark is a backdoor to its neighbour. Fagaras gives two hundred eleven, Pitesti one hundred one, Craiova two hundred thirty-nine, each matching the true distance to Bucharest. Across all pairs with eight landmarks, the estimate is exact on three hundred and sixty of three hundred and eighty. Exact where the landmark allows it, safe everywhere else.

## 19 · Does the estimate stay stable?

Start: 389.38s · Visual duration: 25.07s

There is a local test that matters to the search itself. Step from one city to a neighbour. The estimated remaining distance may change, but it cannot jump by more than the cost of that single road. Our estimate passes this test on every road and for every goal. This property is called consistency, and it is stronger than admissibility. Yet the search does not rely on it. Whenever a cheaper route to a city is found, that city is reopened rather than trusted. Optimality rests only on admissibility; stability is a measured bonus.

## 20 · Watch the estimate steer the search.

Start: 414.45s · Visual duration: 19.77s

Return to the query we began with, Arad to Bucharest. Here is A star with the combined estimate, replayed step by step on the map. Watch the frontier. The estimate draws it toward the goal, so the search settles far fewer cities than uninformed uniform cost search. Where uniform cost settles thirteen, this search settles five, and the difference is the guidance. The route it returns is the same one, through Sibiu, Rimnicu Vilcea and Pitesti, and its cost is unchanged at four hundred eighteen kilometres. Guidance changes the work, not the answer.

## 21 · Does the estimate cut the work?

Start: 434.22s · Visual duration: 15.73s

Averaged over all pairs, uninformed uniform cost search expands about eleven cities. A star with the LP estimate expands about six. Adding the landmark bound brings that to about five, roughly half of the uninformed search, while the returned route stays optimal. Greedy best-first expands even fewer, about five, but it ignores the cost already paid. It returns a suboptimal route on sixty-one of the three hundred eighty pairs. The ensemble keeps greedy's guidance without giving up optimality: that is what the proof upstream buys us.

## 22 · How often does guidance reduce work?

Start: 449.95s · Visual duration: 14.80s

Averages can hide the details, so plot every pair. On one axis, the cities settled by uninformed uniform cost search. On the other, the cities settled by A star with the combined estimate. The diagonal marks equal work. Almost every point falls below it: A star settles strictly fewer cities on three hundred fifty-two of the three hundred eighty pairs, the same number on twenty-eight, and never more. The guidance is not a lucky average; it holds pair by pair.

## 23 · Do the guided searches stay optimal?

Start: 464.75s · Visual duration: 15.43s

Cutting work is only useful if the answer stays correct. Compare each search's returned cost against the true shortest distance, over all three hundred and eighty pairs. Uniform cost search is optimal on every pair, as expected. So are A star with the LP bound, A star with the landmark bound, their combination, and bidirectional A star. Each returns the optimal cost on all three hundred and eighty. Greedy best-first, which ignores the cost already paid, is optimal on only three hundred and nineteen. The admissible bounds keep the speed without losing correctness.

## 24 · Why does a safe estimate keep A* optimal?

Start: 480.18s · Visual duration: 18.43s

A safe estimate is not just a good guess; it is what keeps the answer correct. Suppose A star selects a goal whose cost is above the true optimum. The cheaper route still exists, so some city on it remains in the frontier. For that city, the cost already paid plus the estimate equals at most the optimum, because the estimate never exceeds the true remainder. Its whole-trip value is therefore no larger than the optimum, and the optimum is smaller than the selected goal's cost. A frontier city with a smaller value would have been selected first. That contradiction is why admissibility, however loose the estimate, preserves optimality.

## 25 · Could we search from both ends?

Start: 498.62s · Visual duration: 23.13s

Start one search at Arad and another at Bucharest. Each has its own costs, parents, and frontier. Each uses the combined estimate toward the opposite endpoint. The project alternates forward and backward expansions. The colored branches show discoveries on each side, using the exported project trace. This is bidirectional A star. It may change the amount of work, but it is not guaranteed to be faster. A shared city gives us a complete journey. Does that mean we can stop?

## 26 · Is the first meeting enough?

Start: 521.75s · Visual duration: 22.08s

Two searches meeting is exciting, but it only proves that a route exists. Imagine finding the 450-kilometre journey through Fagaras while the 418-kilometre alternative is still unresolved. The first complete route need not be best. This is an illustration of the stopping problem, not a claim about the first meeting in our recorded run. We keep the cheapest complete route found so far, call its cost mu, and ask whether any cheaper route could remain.

## 27 · When is the answer certain?

Start: 543.83s · Visual duration: 24.07s

The best complete route gives an upper bound: the optimum cannot be more expensive. Before a cheaper route is resolved, each A star frontier retains a representative whose whole-trip estimate is no greater than that route's cost. Reopening improved states preserves this reasoning. If either frontier minimum reaches the candidate cost, a cheaper route is ruled out. The implementation therefore uses the maximum of the two minima, not their sum. The two estimates already refer to the whole journey.

## 28 · Did we save work?

Start: 567.90s · Visual duration: 21.03s

Both methods return the 418-kilometre journey. On this recorded query, compare actual expansions and generated entries. The bidirectional count excludes the synthetic final display frame. Fewer expansions do not necessarily mean fewer generated entries, lower memory, or faster runtime, and preprocessing also has a cost. A twenty-city example cannot establish scaling. What we have gained is a sequence of ideas: explore by cost, guide that exploration with optimism, and certify the result when searching from both ends.