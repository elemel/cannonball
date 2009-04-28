#include <CGAL/Exact_predicates_inexact_constructions_kernel.h>
#include <CGAL/Partition_traits_2.h>
#include <CGAL/partition_2.h>
#include <algorithm>
#include <iostream>
#include <iterator>
#include <vector>

typedef CGAL::Exact_predicates_inexact_constructions_kernel Kernel;
typedef CGAL::Partition_traits_2<Kernel> Traits;
typedef Traits::Point_2 Point;
typedef Traits::Polygon_2 Polygon;
typedef std::vector<Polygon> PolygonVector;

int main()
{
    Polygon polygon;
    std::cin >> polygon;

    PolygonVector partition;
    CGAL::approx_convex_partition_2(polygon.vertices_begin(), 
                                    polygon.vertices_end(),
                                    std::back_inserter(partition));
    std::cout << partition.size() << std::endl;
    std::copy(partition.begin(), partition.end(),
              std::ostream_iterator<Polygon>(std::cout, "\n"));
    return 0;
}

