#pragma once

#include <boost/format.hpp>
#include <boost/geometry.hpp>
#include <boost/geometry/geometries/box.hpp>
#include <boost/geometry/geometries/point.hpp>


namespace spatial_index {

namespace bg = boost::geometry;
namespace bgi = boost::geometry::index;


#ifdef BBPSPATIAL_DOUBLE_PRECISION
using CoordType = double;
#else
using CoordType = float;
#endif

using Point3D = bg::model::point<CoordType, 3, bg::cs::cartesian>;
using Box3D = bg::model::box<Point3D>;


/**
 * \brief An OO augmented point to improve code readability
 *         with sequences of operations
 */
struct Point3Dx: public Point3D {
    using Point3D::Point3D;

    inline Point3Dx(const Point3D& o) noexcept
        : Point3D(o) {}

    inline Point3Dx(Point3D&& o) noexcept
        : Point3D(std::move(o)) {}


    /// Vector component-wise

    // Modify temporaries right away
    inline Point3Dx& operator+(Point3D const& other) && {
        bg::add_point<Point3D>(*this, other);
        return *this;
    }
    inline Point3Dx& operator-(Point3D const& other) && {
        bg::subtract_point<Point3D>(*this, other);
        return *this;
    }
    inline Point3Dx& operator*(Point3D const& other) && {
        bg::multiply_point<Point3D>(*this, other);
        return *this;
    }

    // Return new objects if lvalue
    inline Point3Dx operator+(Point3D const& other) const& {
        Point3Dx copy(*this);
        bg::add_point<Point3D>(copy, other);
        return copy;
    }

    inline Point3Dx operator-(Point3D const& other) const& {
        Point3Dx copy(*this);
        bg::subtract_point<Point3D>(copy, other);
        return copy;
    }

    inline Point3Dx operator*(Point3D const& other) const& {
        Point3Dx copy(*this);
        bg::multiply_point<Point3D>(copy, other);
        return copy;
    }

    inline CoordType dot(Point3D const& o2) const {
        return get<0>() * o2.get<0>() + get<1>() * o2.get<1>() + get<2>() * o2.get<2>();
    }

    inline Point3D cross(Point3D const& other) const {
        return bg::cross_product<Point3D, Point3D, Point3D>(*this, other);
    }


    /// Operations with scalar

    inline Point3Dx& operator+(CoordType val) && {
        bg::add_value<Point3D>(*this, val);
        return *this;
    }
    inline Point3Dx& operator-(CoordType val) && {
        bg::subtract_value<Point3D>(*this, val);
        return *this;
    }
    inline Point3Dx& operator*(CoordType val) && {
        bg::multiply_value<Point3D>(*this, val);
        return *this;
    }
    inline Point3Dx& operator/(CoordType val) && {
        bg::divide_value<Point3D>(*this, val);
        return *this;
    }

    inline Point3Dx operator+(CoordType val) const& {
        Point3Dx copy(*this);
        bg::add_value<Point3D>(copy, val);
        return copy;
    }

    inline Point3Dx operator-(CoordType val) const& {
        Point3Dx copy(*this);
        bg::subtract_value<Point3D>(copy, val);
        return copy;
    }

    inline Point3Dx operator*(CoordType val) const& {
        Point3Dx copy(*this);
        bg::multiply_value<Point3D>(copy, val);
        return copy;
    }

    inline Point3Dx operator/(CoordType val) const& {
        Point3Dx copy(*this);
        bg::divide_value<Point3D>(copy, val);
        return copy;
    }

    /// Self operands

    inline Point3Dx sqrt() const {
        return {std::sqrt(get<0>()), std::sqrt(get<1>()), std::sqrt(get<2>())};
    }

    inline CoordType dist_sq(Point3D const& b) const {
        Point3Dx p = (*this) - b;
        return p.dot(p);
    }

    inline CoordType norm_sq() const {
        return get<0>() * get<0>() + get<1>() * get<1>() + get<2>() * get<2>();
    }

    inline CoordType norm() const {
        return std::sqrt(norm_sq());
    }

    inline Point3D& unwrap() {
        return *this;
    }

    inline bool operator==(Point3D const& rhs) const {
        auto dist2 = dist_sq(rhs);
        if (dist2 == 0.f) return true;
        return dist2 < norm_sq() * 1e-8f;  // relative tolerance
    }
};

//
// Helpers to allow operations with Point3Dx when they'r the second operand
//
template <typename T, typename std::enable_if<!std::is_same<T, Point3Dx>::value, int>::type = 0>
inline Point3Dx operator+(const T& v, const Point3Dx& point) {
    return point + v;
}

template <typename T, typename std::enable_if<!std::is_same<T, Point3Dx>::value, int>::type = 0>
inline Point3Dx operator-(const T& v, const Point3Dx& point) {
    return (point * -1.) + v;
}

template <typename T, typename std::enable_if<!std::is_same<T, Point3Dx>::value, int>::type = 0>
inline Point3Dx operator*(const T& v, const Point3Dx& point) {
    return point * v;
}


inline Point3D max(Point3D const& p1, Point3D const& p2) {
    return Point3D{std::max(p1.get<0>(), p2.get<0>()),
                   std::max(p1.get<1>(), p2.get<1>()),
                   std::max(p1.get<2>(), p2.get<2>())};
}

inline Point3D min(Point3D const& p1, Point3D const& p2) {
    return Point3D{std::min(p1.get<0>(), p2.get<0>()),
                   std::min(p1.get<1>(), p2.get<1>()),
                   std::min(p1.get<2>(), p2.get<2>())};
}

inline std::ostream& operator<<(std::ostream& os, Point3D const& p) {
    os << boost::format("[%.3g %.3g %.3g]") % p.get<0>() % p.get<1>() % p.get<2>();
    return os;
}


}  // namespace spatial_index


// operator== directly on boost Point3D
namespace boost {
namespace geometry {
namespace model {

inline bool operator==(spatial_index::Point3D const& p1,
                       spatial_index::Point3D const& p2) {
    return spatial_index::Point3Dx(p1) == p2;
}

}}}  // namespace boost::geometry::model
