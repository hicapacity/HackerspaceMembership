var $custom = $.noConflict();

(function($){
	var MakerData = function(makers){
		this.makers = {};
		_.each(makers, function(maker, i){
			this.makers[maker.id] = maker;
			this.makers[maker.id].index = i;
			this.makers[maker.id].payments = {};
		}, this);
		this.min = Number.POSITIVE_INFINITY;
		this.max = Number.NEGATIVE_INFINITY;
	};
	MakerData.prototype.addPayments = function(payments){
		_.each(payments, function(payment){
			if (payment.maker in this.makers){
				var maker = this.makers[payment.maker];
				payment.index = maker.index;
				payment.start = payment.start * 1000;
				payment.end = payment.end * 1000;
				maker.payments[payment.id] = payment;

				this.min = Math.min(this.min, payment.start);
				this.max = Math.max(this.max, payment.end);
			} else {
				console.log("got payment not associated with user?");
				console.log(payment);
			}
		}, this);
	};

	MakerData.prototype.getMakers = function(){
		ret = [];
		_.each(this.makers, function(maker){
			ret.push(maker);
		}, this);
		return ret;
	};

	MakerData.prototype.getPayments = function(){
		ret = [];
		_.each(this.makers, function(maker){
			_.each(maker.payments, function(payment){
				ret.push(payment);
			}, this);
		}, this);
		return ret;
	};

	var create_member_chart = function(makerData){
		var $chart = $("#membership_chart");
		var makers = makerData.getMakers();
		var h = 20;
		var h_pad = 5;
		var height = makers.length * (h + h_pad);
		var width = parseInt($chart.css("width"), 10);
		var minDate = new Date(makerData.min);
		var maxDate = new Date(makerData.max);

		var chart = d3.select("#membership_chart").append("svg")
			.attr("class", "chart")
			.attr("width", width)
			.attr("height", height + 100);

		var x = d3.time.scale().range([width - 100, 0]);
		var xAxis = d3.svg.axis()
			.scale(x)
			.tickSize(-height)
			.tickSubdivide(3);
		x.domain([minDate, maxDate]);

		chart.append("svg:g")
			.attr("class", "x grid")
			.attr("transform", "translate(100," + height + ")")
			.call(xAxis);
		
		chart.selectAll("text")
			.data(makerData.getMakers(), function(d){ return d.index; })
			.enter().append("text")
				.attr("x", 0)
				.attr("y", function(d){ return 15 + d.index * (h + h_pad); })
				.text(function(d){ return d.name; });

		chart.selectAll("rect")
			.data(makerData.getPayments(), function(d){ return d.index; })
			.enter().append("rect")
				.attr("class", "payment")
				.attr("x", function(d){
					return 100 + x(d.end);
				})
				.attr("y", function(d){ return d.index * (h + h_pad); })
				.attr("height", h)
				.attr("width", function(d){
					return Math.abs(x(d.end) - x(d.start));
				})

	};

	$(document).ready(function(){
		var data = {
			makers: null,
			payment: null
		};
		var on_ajax = function(type, d){
			data[type] = d;
			if (!_.isNull(data["makers"]) && !_.isNull(data["payment"])){
				var makerData = new MakerData(data["makers"]);
				makerData.addPayments(data["payment"]);
				create_member_chart(makerData);
			}
		};
		$.ajax('/admin/membership/report_ajax/', {
			success: function(data, status, xhr){
				on_ajax("makers", data.makers);
			}
		});
		$.ajax('/admin/payment/report_ajax/', {
			success: function(data, status, xhr){
				on_ajax("payment", data.payments);
			}
		});
	});
})($custom);
